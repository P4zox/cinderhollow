// ------------------------------------------------------------------ WM: the move-table engine (docs/WEAPON_REVAMP.md Part A)
// Each of the 9 weapon types registers its table in a 76_mech_*.js file: mvRegister(type, T, moves).
//  * A move is a row of the table: dmg (per hit) / n or hits[] / poise (whole move) / stam / wind / total (ms), plus box,
//    lunge, flags and hooks. It becomes ATK[id] (the state id the player plays), so every older reader keeps working.
//  * Moves run on their own clock (P.mvT, ms, scaled by attack speed): the hit lands at `wind`, you can act again at
//    `total`. The animation tag (the real WA tag if the sheet has it, else the nearest existing one, pHas) is time-mapped
//    so its first active frame lands on the wind-up and its last frame on the total.
//  * Inputs pressed during a move are queued (J / K / I) and played at `total` along the move's `next` routes
//    (branches, holds); otherwise the 180 ms buffer applies as everywhere else. L cancels a move once its hit has
//    come out, unless the move is `commit`.
//  * Rank-gated moves (move.rank) don't exist below that Mastery rank (masteryRank(type), 1 if WS's API is missing).
const MV = { rank: null, types: {}, defs: {}, order: [] };
const MV_SR = 40;   // "sword reach": the Longsword's light reaches 40 px ahead (36 px drawn x the old 1.12 reach bonus)
const MV_STATES = {};   // type states that aren't attacks: sheathe, iai stance, brace, vault, grapple, demon toggle ...
const WEAPON_UNLOCKS = {};   // type -> [{ rank, id, name, input, desc }] (WS's mastery screen renders it)
const MOVESETS_TYPES = ['longsword', 'katana', 'greatsword', 'maul', 'sns', 'dual', 'spear', 'staff', 'whip'];

// ---- type / rank / mastery
function mvType() {
  let t = null;
  try { t = typeof wtype === 'function' ? wtype() : null; } catch (e) {}
  if (MV.types[t]) return t;
  const c = wcls(); return MV.types[c] ? c : 'longsword';
}
function mvT() { return MV.types[mvType()] || MV.types.longsword; }
function mvRank(type) {
  if (MV.rank != null) return MV.rank;
  try { if (typeof masteryRank === 'function') return masteryRank(type || mvType()) || 1; } catch (e) {}
  return 1;
}
function mvHas(r) { return !r || mvRank() >= r; }
function mvGain(why) { try { if (typeof masteryGain === 'function') masteryGain(mvType(), 5, why); } catch (e) {} MV.gains = (MV.gains || 0) + 1; MV.lastGain = why; }
function mvOn(type) { return mvType() === type; }
// the boss hurtbox padding (04b_sigs.js had it; kept here so it survives SIGS' removal)
function hbOf(t) { const hb = t.hurtbox(); if (!hb || !t.boss) return hb; return rect(hb.x0 - 8, hb.y0 - 6, hb.x1 + 8, hb.y1); }
// the animation tag a move id plays (24_secrets' arsenal copies use tags, the move ids may differ: attack4 -> riposte)
function mvAnimTag(id) { const A = ATK[id]; return A && A.mv ? mvResolve(A).tag : id; }
function isFinisher(state) { const A = ATK[state]; return !!(A && A.mv && A.mv.fin); }

// ---- registration
function mvRegister(type, T, moves) {
  T.id = type; MV.types[type] = T; MV.order.push(type);
  for (const [id, d] of Object.entries(moves)) mvDef(type, id, d);
  MOVESETS[type] = { combo: T.light.slice(), extra: T.light[T.light.length - 1], heavy: T.heavyTag || T.K || T.light[0], up: T.up, air: T.air, down: T.down };
  WEAPON_UNLOCKS[type] = (T.unlocks || []).map(u => ({ ...u }));
}
function mvDef(type, id, d) {
  d.id = id; d.type = type; MV.defs[id] = d;
  if (d.hits) d.n = d.hits.length;
  d.n = d.n || 1; d.kind = d.kind || 'light';
  const A = ATK[id] = { mv: d, mult: d.hits ? Math.max(...d.hits) : d.dmg || 0, poise: d.poise || 0, cost: typeof d.stam === 'number' ? d.stam : 0, staffSpin: !!d.staffSpin, kind: d.kind, cls: type, speed: 1, lunge: d.lunge || 0,
    fx: d.fx === undefined ? null : d.fx, fxAt: [18, -17], up: !!d.up, air: !!d.air, down: !!d.down, spin: !!d.spin, big: !!(d.fin || d.big || d.kind === 'heavy'),
    counter: !!d.counter, commit: !!d.commit, hang: !!d.hang, active: [2, 3], reach: [-2, MV_SR], ys: [-36, -2] };
  return A;
}
// pick the animation tag and build the time map (lazy: the sheet is only queried once the game runs)
const MV_PAD = h => { if (!h) return h; let [x0, y0, x1, y1] = h; if (y1 - y0 < 18) { const c = (y0 + y1) / 2; y0 = Math.min(y0, c - 9); y1 = Math.min(2, Math.max(y1, c + 9)); } return [Math.min(x0, x1 - 14), y0, x1, y1]; };
function mvResolve(A) {
  if (A._r && A._r.ok === pSheet().ok) return A._r;
  const d = A.mv, sh = pSheet();
  const real = d.tags.find(t => pHas(t));
  const tag = real || 'attack1';
  const PM = (typeof ASSETS !== 'undefined' && ASSETS.player_meta && ASSETS.player_meta.moves) || {}, m = PM[tag] || {};
  const tg = sh.ok && sh.tag(tag), durs = [];
  if (tg) for (let i = tg.from; i <= tg.to; i++) durs.push(sh.frames[i].ms || 100); else durs.push(100, 100, 100, 100);
  const n = durs.length, cum = [0]; for (const x of durs) cum.push(cum[cum.length - 1] + x);
  const act = (m.active || [Math.min(2, n - 1), Math.min(3, n - 1)]).map(i => clamp(i, 0, n - 1));
  if (d.hitFrame !== undefined) act[0] = act[1] = clamp(d.hitFrame, 0, n - 1);
  const R = { ok: sh.ok, tag, real: real === d.tags[0], n, cum, tHit: cum[act[0]], tTot: cum[n], act };
  // active time per hit, mapped into the move's own clock
  const post = Math.max(1, d.total - d.wind), span = Math.max(1, R.tTot - R.tHit);
  R.actMs = d.act || clamp((cum[act[1] + 1] - cum[act[0]]) * post / span, 45, 130);
  // the hitbox: the table's reach where it gives one, else the drawn frame's box (+ the old 1.12 forward bonus)
  let hb = MV_PAD(m.hit) || [-2, -36, 36, -2];
  let x0 = hb[0], x1 = hb[2] * (d.up || d.down ? 1 : 1.12), y0 = hb[1], y1 = hb[3];
  if (d.reach) x1 = d.reach;
  if (d.spin) x0 = -(d.backReach || x1 * 0.85);
  else if (d.back) x0 = -d.back;
  if (d.ys) { y0 = d.ys[0]; y1 = d.ys[1]; }
  if (d.box) [x0, x1, y0, y1] = d.box;
  A.reach = [x0, x1]; A.ys = [y0, y1]; A.active = act.slice();
  A.fxAt = m.fxAt || [18, -17];
  // multi-hit moves: the art's own hit frames (meta.hits), mapped into the move's clock (else wind + k * gap)
  const inv = tau => tau <= R.tHit ? (R.tHit > 0 ? tau / R.tHit * d.wind : d.wind) : d.wind + (tau - R.tHit) / span * post;
  if (d.n > 1 && real && !d.animLoop && m.hits && m.hits.length === d.n) R.hitT = m.hits.map(f => inv(cum[clamp(f, 0, n - 1)]));
  A._r = R; return R;
}

// ---- starting a move
// o: { cost (stamina override), mul (damage x), t0 (start the clock here), step (combo index), perfect, lv, ... }
function mvStart(id, o = {}) {
  const A = ATK[id]; if (!A || !A.mv) return false;
  const d = A.mv;
  if (d.rank && !mvHas(d.rank)) return false;
  if (d.can && !d.can(o)) return false;
  // an airborne attack counts toward the air limit (AIR_CHAIN) however it starts (neutral, queued, a follow-up)
  const airAtk = !P.ground && !d.noAirCount && (d.air || d.up || d.down || d.airCount);
  if (airAtk && P.airLock && !(typeof DBS !== 'undefined' && DBS.inWater)) { if (!P.airDenied) { P.airDenied = true; sfx.deny(); } return false; }
  const R = mvResolve(A);
  let cost = o.cost !== undefined ? o.cost : (typeof d.stam === 'function' ? d.stam(o) : d.stam || 0);
  if (A.kind === 'heavy' && charmOn('c_brand')) cost *= 0.8;   // Brand of the Forge: heavies cost 20% less
  if (cost) spend(cost);
  if (P.mvQ2) { buffered.set(P.mvQ2.b === 'J' ? 'attack' : 'heavy', performance.now()); P.mvQ2 = null; }
  P.hitSet = new Set(); P.mvT = o.t0 || 0; P.mvHitK = -1; P.mvQ = null; P.mvO = o; P.mvMul = o.mul || 1; P.mvGained = false;
  P.mvLunge = d.lungeFn ? d.lungeFn(o) : d.lunge || 0;
  // a plain swing only steps its full distance when you push forward (half standing still); dash moves (own lungeLead) always do
  if (P.mvLunge > 0 && d.lungeLead === undefined && !d.dash && inputX() !== P.face) P.mvLunge *= 0.5; P.counterMul = o.counterMul || 1; P.charged = !!o.charged; P.charge = o.charge || 0; P.pogoed = false; P.mvLv = o.lv || 0;
  P.comboStep = o.step !== undefined ? o.step : (d.step !== undefined ? d.step : -1);
  if (d.step === 0) P.combo = 1; else if (d.step > 0) P.combo = d.step + 1;
  const loop = !!((d.loop || d.animLoop) && R.real);
  setP(id, R.tag, loop, loop ? 1 : 0);
  if (!loop) { P.anim.speed = 0; if (d.loop) { P.anim.i = Math.max(0, R.act[0] - 1); P.anim.t = 0; } }
  P.mvGround0 = P.ground;
  if (airAtk && !(typeof DBS !== 'undefined' && DBS.inWater)) { airAtkStart(); P.mvAirFrame = P.clk; }
  if (d.on && d.on.start) d.on.start(A, o);
  const T = MV.types[d.type]; if (T && T.started) T.started(A, o);
  MV.last = id;
  return true;
}
function mvStartLight(o = {}) {
  const T = mvT(); if (held.has('up') && T.up) return mvStart(T.up);
  return mvStart(T.light0 ? T.light0() : T.light[0], { step: 0, ...o });
}
function mvNeutralK(ax) { const T = mvT(); if (T.onK) return T.onK(ax); return mvStart(T.K); }
function mvCounter() { const T = mvT(); const id = T.counter ? T.counter() : null; if (!id || !ATK[id]) return false; if (!mvStart(id, { counterMul: P.counterBonus || 1 })) return false; P.gcT = 0; P.counterBonus = 0; sfx.glint(); spawnFx(fxOr('parry_flash', 'parry_spark'), P.x + P.face * 10, P.y - 18, P.face, null, { alpha: 0.6 }); return true; }

// ---- neutral: J / K / I from a free state (04_player's canStart block)
function mvNeutral(ax) {
  const T = mvT(), air = !P.ground;
  if (peek('attack') && P.st > 0) {
    if (T.onJ && T.onJ(ax)) return true;
    if (!air && P.gcT > 0 && mvCounter()) { take('attack'); return true; }
    take('attack'); if (ax) P.face = ax;
    if (held.has('up') && T.up) return mvStart(T.up) || true;
    if (air) {
      if (held.has('down') && T.down) return mvStart(T.down) || true;
      if (T.airRise && P.vy < -30 && T.airRise()) return true;
      return mvStart(T.air) || true;
    }
    if (P.dgEnd && P.clk - P.dgEnd.t < 0.25 && mvRollJ(P.dgEnd.g)) { P.dgEnd = null; return true; }
    if (P.mvChain && P.clk - P.mvChain.t < 0.3) {   // a press just after a move ended still continues its chain
      const c = P.mvChain, A = ATK[c.id]; P.mvChain = null;
      if (A) { const q = { b: 'J', t: A.mv.total + (P.clk - c.t) * 1000, at: P.clk, after: (P.clk - c.t) * 1000 }, nx = mvNext(A, q); if (nx && mvGo(nx, typeof nx === 'string' && nx[0] !== '@' ? { perfect: mvPerfect(q, A) } : undefined)) return true; }
    }
    return mvStartLight() || true;
  }
  if (peek('heavy') && P.st > 0) {
    if (air) {
      if (T.onAirK && T.onAirK(ax)) return true;
      if (P.state !== 'wall' && pHas('plunge') && smashReady()) { take('heavy'); if (ax) P.face = ax; smashStart(); startPlunge(); return true; }
      return false;
    }
    take('heavy'); if (ax) P.face = ax;
    if (P.dgEnd && P.clk - P.dgEnd.t < 0.25 && T.rollK && T.rollK(P.dgEnd.g)) { P.dgEnd = null; return true; }
    if (P.mvChain && P.clk - P.mvChain.t < ((ATK[P.mvChain.id] && ATK[P.mvChain.id].mv.chainK) || 300) / 1000) {
      const c = P.mvChain, A = ATK[c.id]; P.mvChain = null;
      if (A) { const nx = mvNext(A, { b: 'K', t: A.mv.total + (P.clk - c.t) * 1000, at: P.clk - 0.01, after: (P.clk - c.t) * 1000 }); if (nx && nx !== '@K' && mvGo(nx)) return true; }
    }
    return mvNeutralK(ax) || true;
  }
  if (peek('parry')) {
    if (T.onI) return T.onI(ax);
    if (P.ground && P.st > 0) { take('parry'); startParry(); return true; }
  }
  return false;
}
// start the result of a route: a move id, or '@J' / '@K' / '@I' (that button from neutral)
function mvGo(nx, o) {
  if (!nx) return false;
  if (typeof nx === 'object') return mvStart(nx.id, nx);
  if (nx === '@J' || nx === '@K') { buffered.set(nx === '@J' ? 'attack' : 'heavy', performance.now()); return mvNeutral(inputX()); }
  if (nx === '@I') { const T = mvT(); if (T.onI) { buffered.set('parry', performance.now()); return T.onI(inputX()); } if (P.ground) { startParry(); return true; } return false; }
  return mvStart(nx, o || {});
}
// where a queued press (q = { b: 'J' | 'K' | 'I', t: ms into the move, at: P.clk }) leads from move A
function mvNext(A, q) {
  const d = A.mv, r = d.next && d.next[q.b];
  let nx = typeof r === 'function' ? r(q, A) : r;
  if (typeof nx === 'string' && nx[0] !== '@' && ATK[nx] && ATK[nx].mv.rank && !mvHas(ATK[nx].mv.rank)) nx = null;
  if (nx === undefined || nx === null) nx = '@' + q.b;
  return nx;
}
// "perfect timing": the press came in the last 150 ms of the move (or within 80 ms after it)
function mvPerfect(q, A) { const late = A.mv.total - q.t; return (late >= -34 && late <= 150) || (q.after !== undefined && q.after <= 80); }   // -34: a press on the move's last frame
function mvHeldK(q, ms = 150) { return held.has('heavy') && q.b === 'K' && (P.clk - q.at) * 1000 >= ms; }

// ---- the per-frame update of a move (04_player: case 'ATTACK')
function mvSpeed(A) { const T = MV.types[A.cls]; return T && T.speed ? T.speed(A) : 1; }
function mvFrame(A) {
  const R = A._r, an = P.anim, d = A.mv; if (!R) return;
  const t = P.mvT;
  let tau = t <= d.wind ? (d.wind > 0 ? t / d.wind * R.tHit : R.tHit) : R.tHit + Math.min(1, (t - d.wind) / Math.max(1, d.total - d.wind)) * (R.tTot - R.tHit);
  tau = clamp(tau, 0, R.tTot - 0.01);
  let i = 0; while (i < R.n - 1 && tau >= R.cum[i + 1]) i++;
  if (i !== an.i) { an.i = i; an.changed = true; }
  an.t = Math.min(tau - R.cum[i], an.ms(i) - 0.01); an.done = false; an.speed = 0;
}
function mvUpdate(dt, ax, grav) {
  const A = ATK[P.state], d = A.mv, an = P.anim;
  if (!d) { setP('idle', 'idle', true); return; }
  const T = MV.types[d.type] || {}, R = mvResolve(A);
  const spd = mvSpeed(A), t0 = P.mvT;
  P.mvT += dt * 1000 * spd;
  const t = P.mvT, W = d.wind;
  if (d.on && d.on.update) { const r = d.on.update(dt, A, ax, grav); if (r === 'stop' || P.state !== d.id) return; }
  if (d.loop) { if (!R.real) { an.i = Math.max(0, R.act[0] - 1); an.t = 0; an.speed = 0; an.done = false; } mvQueue(A); return; }
  if (!(d.animLoop && R.real)) mvFrame(A);
  // movement: a lunge covers d.lunge px between just before the hit and just after it; otherwise ground friction
  const lw0 = Math.max(0, W - (d.lungeLead ?? 120)), lw1 = W + (d.lungeTail ?? 40);
  if (d.move) d.move(dt, A, ax, grav);
  else if (P.ground) {
    if (P.mvLunge && t >= lw0 && t < lw1) P.vx = P.face * P.mvLunge / ((lw1 - lw0) / 1000) * spd;
    else if (P.mvLunge && t0 < lw1 && t >= lw1) P.vx *= 0.15;   // the step ends planted: no slide past the lunge
    else P.vx *= Math.pow(0.0002, dt);
    grav();
  }
  else if (d.hang && t < W + 150) { P.vx *= Math.pow(0.02, dt); P.vy = Math.min(Math.max(P.vy, 0) + GRAV_DN * 0.2 * dt, 50); }   // hangs: the rise stops for the heave
  else if (d.down) { P.vx = approach(P.vx, ax * MAXV * 0.6, 500 * dt); grav(); }
  else { if (P.mvLunge && t >= lw0 && t < lw1) P.vx = P.face * P.mvLunge / ((lw1 - lw0) / 1000) * spd; else P.vx = approach(P.vx, ax * MAXV * 0.8, 500 * dt); grav(); }
  // hits: hit k starts at wind + k * gap (each one a fresh pass over the targets)
  const n = d.n, gap = d.gap || 70, hitAt = k => (R.hitT ? R.hitT[k] : W + k * gap);
  for (let k = P.mvHitK + 1; k < n; k++) {
    if (t < hitAt(k)) break;
    P.mvHitK = k; P.hitSet = new Set();
    if (k === 0) mvSwing(A); else { (d.kind === 'heavy' ? sfx.swing : sfx.swing)(); if (d.fxEach && A.fx) spawnFx(fxOr(A.fx, 'slash'), P.x + P.face * A.fxAt[0], P.y + A.fxAt[1], P.face); }
    if (d.on && d.on.hitStart) d.on.hitStart(k, A);
  }
  if (P.mvHitK >= 0 && !d.noHit) {
    const k0 = hitAt(P.mvHitK), act = n > 1 ? Math.min(R.actMs, (P.mvHitK + 1 < n ? hitAt(P.mvHitK + 1) - k0 : gap) - 1) : R.actMs;
    if (t <= k0 + act) playerStrike(A);
  }
  if (P.state !== d.id) return;
  mvQueue(A);
  // cancels: L once the hit is out (not on commit moves); a double jump out of an air move's recovery
  if (t >= W && !d.commit && peek('roll') && P.st > 0 && (P.ground || P.airDash)) { take('roll'); P.mvQ = null; mvDodgeStart(ax); return; }
  if (!P.ground && t >= W + R.actMs && peek('jump') && P.airJumps > 0) { take('jump'); P.airJumps--; doJump(JUMP_V * 0.9, true); return; }
  if (t >= d.total) return mvEnd(A);
  if (P.mvGround0 && !P.ground && !(d.air || d.down || d.up || d.airOk) && P.vy > 60) return mvEnd(A, true);   // walked off a ledge mid-swing
}
function mvSwing(A) {
  const d = A.mv, an = P.anim;
  if (!(d.animLoop && A._r && A._r.real)) { an.i = A.active[0]; an.t = 0; } an.changed = true;
  if (A.fx) spawnFx(fxOr(A.fx, 'slash'), P.x + P.face * A.fxAt[0], P.y + A.fxAt[1], P.face, null, A.up ? { bottom: true } : {});
  (A.kind === 'heavy' || A.big ? sfx.heavySwing : sfx.swing)();
  if (A.kind === 'heavy' && P.charged && has('charged_arts')) fireProjectile('crescent');
  if (d.slam) { shake = Math.max(shake, 6); sfx.boom(); spawnFx('shockwave', P.x + P.face * 22, P.y, 1); spawnFx('ground_crack', P.x + P.face * 22, P.y, 1); for (let i = 0; i < 12; i++) particles.push({ x: P.x + P.face * 22 + rand(-16, 16), y: P.y - 2, vx: rand(-80, 80), vy: -rand(30, 110), g: 320, life: 0.6, kind: 'dust' }); }
  if (d.on && d.on.swing) d.on.swing(A);
}
// latch J / K / I pressed during a move (played at its total). One press is queued (a second waits for the next
// move and is judged there). On a finisher (or the last step of a chain), a press that would START A NEW chain only
// latches in the move's last MV_QFIN ms: mashing through a finisher ends the combo there instead of rolling straight
// into the next one. Earlier presses are dropped. Presses that continue the chain latch from 30 ms in, as before.
const MV_QFIN = 120;
function mvRouted(A, b) {   // does button b continue A's chain (vs falling back to a fresh neutral press)?
  const d = A.mv, r = d.next && d.next[b];
  if (!r) return false;
  if (typeof r === 'string') return r !== '@' + b;
  if (typeof r === 'object') return true;
  try { const nx = r({ b, t: P.mvT, at: P.clk, peek: true }, A); return !!nx && nx !== '@' + b; } catch (e) { return true; }
}
function mvQueue(A) {
  if (P.mvT < 30) return;
  if (P.mvQ) {   // one more press waits for the next move, which re-judges it with its own rules (so J J J typed fast
    // still plays three cuts, but nothing carries on past a finisher)
    if (!P.mvQ2) { if (take('attack')) P.mvQ2 = { b: 'J' }; else if (take('heavy')) P.mvQ2 = { b: 'K' }; }
    return;
  }
  const d = A.mv, ender = d.fin || (d.step !== undefined && !(d.next && d.next.J)), late = d.total - P.mvT <= MV_QFIN;
  const want = b => !ender || late || mvRouted(A, b);
  if (peek('attack')) { take('attack'); if (want('J')) P.mvQ = { b: 'J', t: P.mvT, at: P.clk, up: held.has('up') }; }
  else if (peek('heavy')) { take('heavy'); if (want('K')) P.mvQ = { b: 'K', t: P.mvT, at: P.clk }; }
  else if (d.next && d.next.I && take('parry')) P.mvQ = { b: 'I', t: P.mvT, at: P.clk };
  if (P.mvQ && d.onQueue) d.onQueue(P.mvQ, A);
}
function mvEnd(A, fell) {
  const d = A.mv, q = P.mvQ; P.mvQ = null;
  if (d.on && d.on.end) d.on.end(A);
  if (P.state !== d.id) return;   // the end hook started something else
  if (q && !fell && P.st > 0) {
    const ax = inputX(); if (ax && !d.keepFace) P.face = ax;   // each step of a chain can turn round
    if (q.b === 'J' && q.up && MV.types[d.type].up && !(d.next && typeof d.next.J === 'function')) { if (mvStart(MV.types[d.type].up)) return; }
    const nx = mvNext(A, q);
    if (nx && typeof nx === 'string' && nx[0] !== '@') { const o = { perfect: mvPerfect(q, A) }; if (mvStart(nx, o)) return; }
    setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground);
    if (mvGo(nx)) return;
  }
  P.mvChain = { id: d.id, t: P.clk };
  P.combo = 0; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground);
}
function mvInterrupted() { P.mvQ = null; P.mvQ2 = null; P.mvChain = null; const T = mvT(); if (T.interrupted) T.interrupted(); }

// ---- hitting
function mvRect(A) {
  const top = A.up ? A.ys[0] : A.ys[0];
  return rect(P.x + P.face * A.reach[0], P.y + top, P.x + P.face * A.reach[1], P.y + A.ys[1]);
}
function mvHitCtx(t, hb, A, r) {
  const d = A.mv || {}, T = MV.types[A.cls] || {}, heavy = A.kind === 'heavy';
  const cx = (hb.x0 + hb.x1) / 2, k = Math.max(0, P.mvHitK || 0);
  const c = { t, hb, A, d, k, skip: false, tip: false };
  c.mul = (d.hits ? d.hits[Math.min(k, d.hits.length - 1)] : d.dmgFn ? d.dmgFn() : A.mult) * (P.mvMul || 1);
  c.poise = (d.poiseFn ? d.poiseFn() : A.poise / (d.n || 1)) * skPoiseMul(A) * (heavy ? 1 + (SAVE.stats.str - 10) * 0.015 : 1);
  c.dir = A.spin || d.back ? (cx > P.x ? 1 : -1) : P.face;
  c.x = clamp(A.spin || d.back ? cx : (r.x0 + r.x1) / 2, hb.x0 + 3, hb.x1 - 3);
  c.y = clamp(P.y + (A.ys[0] + A.ys[1]) / 2, hb.y0, hb.y1);
  if (T.hitMod) T.hitMod(c);
  if (d.mod) d.mod(c);
  c.poise = mvPoiseFor(t, c.poise, A, c.y);
  return c;
}
function mvPoiseFor(t, poise, A, y) { const T = mvT(); return T.poiseMod ? T.poiseMod(t, poise, A, y) : poise; }
function mvOnHit(t, info, A, c) {
  const d = A.mv || {}, T = MV.types[A.cls] || mvT();
  if (A.counter && !P.mvGained && t && !t.prop) { P.mvGained = true; mvGain('counter'); }
  if (d.launch && t && !t.boss && !t.prop && t.alive !== false && !(t.cfg && (t.cfg.elite || t.cfg.flying)) && t.vy !== undefined) { t.vy = -d.launch; if (t.breakStance && t.state !== 'stagger') t.breakStance(); }
  if (d.reel && t && !t.boss && !t.prop && t.alive !== false && t.breakStance && !(t.cfg && t.cfg.elite) && t.state !== 'stagger') t.breakStance();
  if (d.on && d.on.hit) d.on.hit(t, info, A, c);
  if (T && T.onHit) T.onHit(t, info, A, c);
}
// a ground AoE around the player (maul plunge, earthshaker, thunderclap ...)
function mvShockwave(o) {
  const r = rect(P.x - o.r, P.y - (o.h || 30), P.x + o.r, P.y + 2);
  spawnFx('shockwave', P.x, P.y, 1); shake = Math.max(shake, o.shake || 6);
  for (let i = 0; i < 16; i++) particles.push({ x: P.x + rand(-o.r, o.r), y: P.y - 2, vx: rand(-80, 80), vy: -rand(30, 110), g: 320, life: 0.6, kind: o.pk || 'dust' });
  const A = ATK[P.state] || PLUNGE_A;
  for (const t of targets()) {
    const hb = hbOf(t); if (!hb || !overlap(r, hb)) continue;
    const info = { dmg: outgoing(D.light, o.dmg, 'melee'), poise: mvPoiseFor(t, o.poise || 0, A, P.y - 10), dir: t.x > P.x ? 1 : -1, kind: 'heavy', x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, melee: true, big: true, fire: !!o.fire };
    t.hit(info); runHooks('strike', t, { dmg: info.dmg, heavy: true, x: info.x, y: info.y }, A);
    if (o.onHit) o.onHit(t, info);
  }
}

// ---- dodges (every type's L): roll, sidestep, heavy roll, backhop, hop, demon dash
// g: { stam, total (ms), inv (s), dist (px), move (ms travelling), back (moves backwards), hop (vy), tags, chain }
function mvDodgeStart(ax) {
  const T = mvT();
  if (T.onL && T.onL(ax)) return true;
  return mvDodge(T.dodge ? (typeof T.dodge === 'function' ? T.dodge(ax) : T.dodge) : MV_ROLL, ax);
}
const MV_ROLL = { stam: 16, total: 420, inv: 0.28, dist: 74, tags: ['roll'] };
function mvDodge(o, ax) {
  if (P.st <= 0) return false;
  spend(o.stam * (has('quickstep') ? 0.7 : 1));
  let dir;
  if (o.back) { dir = ax ? ax : -P.face; if (ax === P.face) dir = -P.face; }   // the backhop always goes away from where you face
  else { if (ax) P.face = ax; dir = o.dir || P.face; if (o.hopDir && !ax) dir = -P.face; }
  P.combo = 0; P.sw = false; P.mvQ = null; P.mvChain = null;
  P.airRoll = !P.ground; if (P.airRoll) P.airDash = false;
  const g = P.dg = { ...o, t: 0, dir, start: P.clk, move: o.move || o.total * 0.72, perfect: false, kind: o.kind || 'roll', ax };
  const tag = P.airRoll && SAVE.items.emberdash && pHas('ember_dash') && !o.keepTag ? 'ember_dash' : (o.tags || ['roll']).find(x => pHas(x)) || 'roll';
  const sh = pSheet(), tg = sh.ok && sh.tag(tag); let tot = 430; if (tg) { tot = 0; for (let i = tg.from; i <= tg.to; i++) tot += sh.frames[i].ms; }
  setP('roll', tag, false, tot / o.total);
  if (o.hop && P.ground) { P.vy = -o.hop; P.ground = false; }
  P.vx = dir * g.dist / (g.move / 1000); sfx.roll(); P.ghostT = 0;
  if (P.ground) spawnFx('dust', P.x - dir * 6, P.y, P.face);
  const T = mvT(); if (T.dodged0) T.dodged0(g);
  return true;
}
function mvRollUpdate(dt, ax, grav) {
  const g = P.dg; if (!g) { setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); return; }
  g.t += dt * 1000;
  const T = mvT(), moving = g.t < g.move;
  if (moving) P.vx = g.dir * g.dist / (g.move / 1000) * (charmOn('c_heel') ? 1.1 : 1);
  else P.vx = approach(P.vx, inputX() * MAXV * 0.6, 900 * dt);
  if (P.airRoll && moving && !g.hop) P.vy = 0; else grav();
  P.ghostT -= dt;
  if (P.ghostT <= 0 && moving && g.ghost !== false) { P.ghostT = 0.035; ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: 0.22 }); }
  if (T.dodgeUpdate && T.dodgeUpdate(dt, g, ax)) return;
  if (P.state !== 'roll') return;
  if (g.t >= g.total * 0.6 && P.ground && peek('jump')) { take('jump'); P.dg = null; doJump(JUMP_V); return; }
  if (g.t >= (g.jAt ?? g.total * 0.4) && P.st > 0 && peek('attack')) { take('attack'); if (mvRollJ(g)) return; }
  if (T.rollK && g.t >= (g.kAt ?? g.total * 0.4) && P.st > 0 && peek('heavy')) { take('heavy'); if (T.rollK(g)) return; }
  if (g.chain && g.t >= g.total * 0.5 && P.st > 0 && peek('roll') && (g.n || 1) < g.chain) { take('roll'); const n = (g.n || 1) + 1; mvDodge({ ...g, n, t: 0 }, ax); if (P.dg) P.dg.n = n; return; }
  if (g.t >= g.total) { P.dgEnd = { t: P.clk, g }; P.dg = null; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); }
}
function mvRollJ(g) {
  const ax = inputX(); if (ax) P.face = ax;
  const T = mvT(); const id = typeof T.rollJ === 'function' ? T.rollJ(g) : T.rollJ;
  if (!id) return false;
  if (typeof id === 'object') return mvStart(id.id, id);
  return mvStart(id, { step: ATK[id] && ATK[id].mv.step });
}
function mvIframes() {
  if (P.mvInv > 0) return true;
  if (P.state === 'roll' && P.dg) { const g = P.dg; return g.t <= g.inv * 1000 + (has('quickstep') ? 50 : 0) + (charmOn('c_heel') ? 50 : 0); }
  const A = ATK[P.state]; if (A && A.mv && A.mv.inv) { const [a, b] = A.mv.inv; return P.mvT >= a && P.mvT <= b; }
  const s = MV_STATES[P.state]; if (s && s.inv && s.inv()) return true;
  return false;
}

// ---- hooks used by 04_player (each defers to the current type)
function mvHurtPre(dmg, dir, id, opt) {
  const c = { dmg, dir, id, opt, front: dir === -P.face, armor: false, negate: false };
  const A = ATK[P.state];
  if (A && A.mv && A.mv.armor) { const a = A.mv.armor; if (a === true || dmg < D.maxHp * a) c.armor = true; if (A.mv.dmgTaken) c.dmg *= A.mv.dmgTaken; }
  const T = mvT(); if (T.hurt) T.hurt(c);
  return c;
}
function mvGuardCost(dmg, opt) {
  const T = mvT();
  if (T.guardCost) return T.guardCost(dmg, opt);
  return { cost: (6 + dmg * 0.8) * (charmOn('c_aegis') ? 0.7 : 1), chip: 0, push: 70, counterT: 0.6 };
}
function mvBlockPose() { const T = mvT(); if (T.blockPose) return T.blockPose(); setP('block', pHas('sh_block') ? 'sh_block' : 'sh_guard', false); }
function mvBlocked(dmg, dir, opt, G, id) { const T = mvT(); if (T.blocked) T.blocked(dmg, dir, opt, G, id); }
function mvDodged(dmg, dir, id, opt) { const T = mvT(); if (T.dodged) T.dodged(dmg, dir, id, opt); }
function mvParryUpdate(dt, ax) { const T = mvT(); return !!(T.parryUpdate && T.parryUpdate(dt, ax)); }
function mvGuardUpdate(dt, ax, grav) { const T = mvT(); return !!(T.guardUpdate && T.guardUpdate(dt, ax, grav)); }
function mvGuardK() { const T = mvT(); return !!(T.guardK && T.guardK()); }
function mvLanded(pre) { const T = mvT(); if (T.landed) T.landed(pre); P.mvAir = false; }
function mvRegenMul() { const T = mvT(); return T.regenMul ? T.regenMul() : 1; }
function mvWalkMul() { const T = mvT(); return T.walkMul ? T.walkMul() : 1; }
function mvIdleTag(want) { const T = mvT(); const t = T.idleTag && T.idleTag(want); return t && pHas(t) ? t : want; }
function mvHealSpeed() { const T = mvT(); return T.healSpeed || 1; }
function mvHealWalk() { const T = mvT(); return T.healWalk || 0; }
function mvPlunge() { const T = mvT(); const p = typeof T.plunge === 'function' ? T.plunge() : T.plunge; return p || { dmg: 1.5, poise: 70, stam: 18 }; }
// run fn after `sec` seconds of play (echo hits, delayed follow-ups); dropped on room change
function mvLater(sec, fn) { MV.later.push({ at: (P.clk || 0) + sec, fn }); }
MV.later = [];
function mvBurn(t, secs, dps) { if (typeof wAddBurn === 'function') wAddBurn(t, secs, dps); else if (t && !t.prop && t.hit) mvLater(0.5, () => { if (t.alive !== false) t.hit({ dmg: dps * secs * 0.5, poise: 0, dir: P.face, kind: 'spell', x: t.x, y: t.y - 12, fire: true }); }); }
// a single strike of `mul` x AR at the box (no move needed): echoes, follow-ups, the whip's thunderclap ...
function mvStrikeAt(box, mul, poise, o = {}) {
  let n = 0; const A = o.A || ATK[P.state] || PLUNGE_A;
  for (const t of targets()) {
    if (o.only && t !== o.only) continue;
    const hb = hbOf(t); if (!hb || !overlap(box, hb)) continue;
    const info = { dmg: outgoing(D.light, mul, 'melee'), poise: mvPoiseFor(t, poise, A, (hb.y0 + hb.y1) / 2), dir: t.x > P.x ? 1 : -1, kind: o.kind || 'light', x: clamp((box.x0 + box.x1) / 2, hb.x0 + 3, hb.x1 - 3), y: (hb.y0 + hb.y1) / 2, melee: true, big: !!o.big, fire: !!o.fire };
    t.hit(info); n++; runHooks('strike', t, { dmg: info.dmg, heavy: info.kind === 'heavy', x: info.x, y: info.y }, A);
    if (o.onHit) o.onHit(t, info);
  }
  return n;
}
function mvTick(dt) {
  P.clk = (P.clk || 0) + dt;
  if (MV.later.length) { const now = MV.later.filter(l => l.at <= P.clk); MV.later = MV.later.filter(l => l.at > P.clk); for (const l of now) try { l.fn(); } catch (e) { console.error(e); } }
  if (P.mvInv > 0) P.mvInv -= dt;
  for (const ty of MV.order) { const T = MV.types[ty]; if (T.tickAll) T.tickAll(dt, ty === mvType()); }
  const T = mvT(); if (T.tick) T.tick(dt);
}

// ---- shared feedback helpers
function mvHudBar(x, y, w, h, f, col, back = 'rgba(10,8,14,0.75)') {
  vctx.fillStyle = back; vctx.fillRect(ox + (x - 0.5) * scale, oy + (y - 0.5) * scale, (w + 1) * scale, (h + 1) * scale);
  vctx.fillStyle = col; vctx.fillRect(ox + x * scale, oy + y * scale, Math.max(0, Math.min(1, f)) * w * scale, h * scale);
}
function mvHudPip(x, y, on, col, r = 1.6) {
  vctx.fillStyle = on ? col : 'rgba(40,34,44,0.85)';
  vctx.beginPath(); vctx.arc(ox + x * scale, oy + y * scale, r * scale, 0, 6.2832); vctx.fill();
}
function mvHudRing(x, y, r, f, col) {   // a ring that drains clockwise (f = 1 full)
  vctx.lineWidth = 1.2 * scale; vctx.strokeStyle = 'rgba(40,34,44,0.9)'; vctx.beginPath(); vctx.arc(ox + x * scale, oy + y * scale, r * scale, 0, 6.2832); vctx.stroke();
  vctx.strokeStyle = col; vctx.beginPath(); vctx.arc(ox + x * scale, oy + y * scale, r * scale, -Math.PI / 2, -Math.PI / 2 + 6.2832 * clamp(f, 0, 1)); vctx.stroke();
}
// the HUD row right of the stamina bar where the types draw their gauges
function mvHudX() { return 10 + clamp(D.maxSt * 0.9, 50, 150) + 6; }
// a 4-point glint (glow layer): the katana's sheathe gleam, the whip's ready crack
function mvStar(x, y, r, col, a = 1) { drawGlow(() => { g.save(); g.globalCompositeOperation = 'lighter'; g.strokeStyle = `rgba(${col},${a})`; g.lineWidth = 1; g.beginPath(); g.moveTo(Math.round(x - r) + 0.5, Math.round(y) + 0.5); g.lineTo(Math.round(x + r) + 0.5, Math.round(y) + 0.5); g.moveTo(Math.round(x) + 0.5, Math.round(y - r) + 0.5); g.lineTo(Math.round(x) + 0.5, Math.round(y + r) + 0.5); g.stroke(); g.fillStyle = `rgba(255,255,255,${a})`; g.fillRect(Math.round(x), Math.round(y), 1, 1); g.restore(); }); }
// the player's silhouette washed in a colour (glow layer, additive): auras
function mvAura(col, a, spread = 1) { const sh = sheet('player'); drawGlow(() => { const o = g.globalCompositeOperation; g.globalCompositeOperation = 'lighter'; for (const dx of [-spread, spread]) drawSprite(sh, P.anim.frame, P.x + dx, P.y, P.face, { alpha: a, flash: 1, flashColor: col }); drawSprite(sh, P.anim.frame, P.x, P.y - spread, P.face, { alpha: a * 0.8, flash: 1, flashColor: col }); g.globalCompositeOperation = o; }); }
function mvSpark(x, y, n, col = '255,240,200', spd = 140) { if (typeof feelSpark === 'function') for (let i = 0; i < n; i++) { const a = rand(0, 6.283); feelSpark(x, y, Math.cos(a) * rand(spd * 0.4, spd), Math.sin(a) * rand(spd * 0.4, spd), col, rand(0.1, 0.22), 160); } }
function mvAfterimage(col = '#dfe6f5', life = 0.35, alpha = 0.55, f) { MV.ghosts.push({ f: f ?? P.anim.frame, x: P.x, y: P.y, face: P.face, life, max: life, col, alpha, wf: f ?? P.anim.frame }); }
MV.ghosts = [];
HOOKS.update.push(dt => { for (const gh of MV.ghosts) gh.life -= dt; if (MV.ghosts.length) MV.ghosts = MV.ghosts.filter(gh => gh.life > 0); });
HOOKS.enter.push(() => { MV.ghosts = []; MV.later = []; if (P) { P.mvChain = null; P.mvQ = null; } });
HOOKS.render.push(() => {
  for (const gh of MV.ghosts) {
    const k = gh.life / gh.max;
    drawSprite(sheet('player'), gh.f, gh.x, gh.y, gh.face, { alpha: gh.alpha * k, flash: 1, flashColor: gh.col });
    const ws = sheet('wpn_' + (SAVE.weapon || 'longsword')); if (ws.ok) drawSprite(ws, gh.wf, gh.x, gh.y, gh.face, { alpha: gh.alpha * k, flash: 1, flashColor: gh.col });
  }
  if (!P) return;
  for (const ty of MV.order) { const T = MV.types[ty]; if (T.renderAll) T.renderAll(ty === mvType()); }
  const T = mvT(); if (T.render) T.render();
});
HOOKS.hud.push(() => { if (!P || !D || typeof state === 'undefined' || state !== 'play') return; const T = mvT(); if (T.hud) T.hud(mvHudX()); });
if (typeof window !== 'undefined' && window.__game) window.__game.mv = { MV, ATK, WEAPON_UNLOCKS, MOVESETS, ev: s => eval(s) };
