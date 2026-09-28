// realistic boss bench (agent WB), modelled on tools/shots/sk/bench.js
// SHOT_HTML=web/dist/wb.html node tools/shots/shot.js tools/shots/wb/bench_real.js tools/shots/wb/out
// A held boss (Gravetusk, max HP set to 3500 so % procs are boss-sized) swings every 2 s: a 1.3 s opening to attack in,
// then a 0.7 s swing the player rolls through. Stamina is real (no refills; a swing is only started if a roll stays
// affordable afterwards), no FP spells.
// Every weapon at +5, neutral spread str 30 / dex 30 / fth 25. Damage is split by source:
//   sig    = anything a SIGS callback did (directly, via the WFX/projectiles it spawned, or burn it applied)
//   status = bleed bursts, frost bursts, burn/rot ticks from the weapon's own buildups
//   melee  = the rest (swings, ripostes)
// far60 = total damage per second dealt with the player pinned 64 px from the boss's hurtbox (nothing should get there
// but a whip tip); farR = signature damage per second pinned at 1.5x the weapon's own melee reach (must be 0).
// Options (define before the body via a wrapper, or edit here): ONLY = [...ids], BENCH_SECS, FAR_SECS, WITH_ART.
await boot(); G.giveArmory(); G.grantTechniques();
const E = G.sk.ev;
const ONLY_ = (typeof ONLY !== 'undefined' && ONLY) || E('Object.keys(WEAPONS)');
const SECS = (typeof BENCH_SECS !== 'undefined' && BENCH_SECS) || 36, FSECS = (typeof FAR_SECS !== 'undefined' && FAR_SECS) || 10;
const ARTMODE = typeof WITH_ART !== 'undefined' ? WITH_ART : true;
const ST = { vig: 35, mnd: 25, end: 25, str: 30, dex: 30, fth: 25 };
// sim clock: input buffering (take/peek) runs on performance.now(); tie it to simulated frames so wall speed can't matter
E(`(() => {
  if (window.__wbI) return;
  const W = window.__wbI = { ctx: 0, projSig: 0, ms: 0 };
  performance.now = () => W.ms;
  W.step = (n, hold = [], tap = []) => { tap.forEach(press); hold.forEach(a => held.add(a)); for (let i = 0; i < n; i++) { W.ms += 1000 / 60; update(1 / 60); } hold.forEach(release); tap.forEach(release); };
  const tagNew = (nW, nP) => { for (let i = nW; i < WFX.length; i++) wrapE(WFX[i]); for (let i = nP; i < projectiles.length; i++) projectiles[i].__sig = 1; };
  const mark = fn => function (...a) { const nW = WFX.length, nP = projectiles.length; W.ctx++; try { return fn.apply(this, a); } finally { W.ctx--; tagNew(nW, nP); } };
  function wrapE(e) { if (!e || e.__sig) return; e.__sig = 1; if (e.update) e.update = mark(e.update); }
  W.wrapSigs = () => { for (const s of Object.values(SIGS)) for (const k of ['swing', 'finisher', 'hit', 'crit', 'dive', 'block']) { const d = Object.getOwnPropertyDescriptor(s, k); if (d && typeof d.value === 'function' && !d.value.__w) { s[k] = mark(d.value); s[k].__w = 1; } } };
  W.wrapSigs();
  const og = outgoing; outgoing = function (b, m, k, src) { if (src && src.__sig) W.projSig = 1; return og.apply(this, arguments); };
  const ab = wAddBurn; wAddBurn = function (t, ...a) { if (t) t.__burnSig = W.ctx > 0; return ab.call(this, t, ...a); };
  W.reach = () => { const ms = moveset(); let r = 0; for (const tag of [...ms.combo, ms.heavy]) { const A = ATK[tag]; if (!A) continue; r = Math.max(r, A.reach[1] * (A.cls ? 1 : D.W.reach) * REACH_MUL); } return r; };
})()`);
const I = () => window.__wbI;
const out = {};
for (const id of ONLY_) {
  const res = { cls: E(`WEAPON_CLASS[${JSON.stringify(id)}]`) };
  for (const phase of ARTMODE ? ['near', 'art', 'far60', 'farR'] : ['near', 'far60', 'farR']) {
    { let seed = 12345; Math.random = () => (seed = (seed * 16807) % 2147483647) / 2147483647; }
    G.SAVE.weapon = id; G.SAVE.weapons[id] = 5;
    if (E(`WEAPON_CLASS[${JSON.stringify(id)}]`) === 'mirror') G.SAVE.lastCls = 'sword';
    G.SAVE.art = E(`(typeof wbArtOf === 'function' ? wbArtOf(${JSON.stringify(id)}) : WEAPONS[${JSON.stringify(id)}].art)`);
    G.give({ stats: { ...ST }, charmsEq: [], skills: [] });
    delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
    G.tp('C5', 6, 10); const b = G.boss;
    for (let i = 0; i < 200 && !b.active; i++) { I().step(4, ['right']); G.P.hp = 99999; if (G.state !== 'play') G.step(1, [], ['pause']); }
    const bx = b.x, by0 = b.y;
    b.update = function (dt) { this.x = bx; this.y = by0; this.commonUpdate(dt); if (this.state === 'stagger') { this.anim.update(dt); this.t -= dt; if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); } } };
    b.state = 'idle'; b.maxHp = 3500; b.hp = 1e7; b.rotT = 0; b._burnT = 0; b._frost = 0; b.bleed = 0; b.stance = 0;
    E('refreshDerived(false); P.hp = D.maxHp * 0.5; P.fp = D.maxFp; P.st = D.maxSt; refillFlasks(); P.cds = {}; hitstop = 0; slowmo = 0; clearBuffer(); P.sigCharge = 0; WFX = []; projectiles.length = 0');
    I().wrapSigs();
    const hb0 = E('hbOf(boss)'), reach = I().reach();
    const gap = phase === 'far60' ? 64 + 8 : phase === 'farR' ? reach * 1.5 + 2 : 0;   // hbOf pads the boss by 8 px
    const px = phase === 'near' || phase === 'art' ? bx - 34 : hb0.x0 - gap;
    G.P.x = px; G.P.face = 1;
    const acc = { melee: 0, sig: 0, status: 0 };
    const oh = b.hit;
    b.hit = function (info) {
      const h0 = this.hp, mul = this.state === 'stagger' && !info.crit ? 1.3 : 1, sig = I().ctx > 0 || I().projSig; I().projSig = 0;
      const r = oh.call(this, info), d = h0 - this.hp;
      if (d > 0) {
        const basePart = Math.min(d, Math.round(info.dmg * mul)), extra = d - basePart;
        if (sig) acc.sig += d; else if (info.kind === 'frost') acc.status += d; else { acc.melee += basePart; acc.status += extra; }
      }
      return r;
    };
    const SEC = phase === 'near' || phase === 'art' ? SECS : FSECS;
    let healed = 0, hp = G.P.hp, arts = 0, heavies = 0, swings = 0, didH = -1, didA = -1;
    const heavyCycHold = (cyc, c, P) => cyc % 3 === 2 && hvCost < G.D.maxSt * 0.6 && didH === cyc && P.state === hvTag && !P.charged && !E('ATK[P.state].noCharge');
    const ltCost = E('ATK[moveset().combo[0]].cost * D.W.stam');
    const hvTag = E('moveset().heavy'), hvCost = E('(ATK[moveset().heavy].staffSpin ? staffSpinCost() : ATK[moveset().heavy].cost * D.W.stam)');
    for (let f = 0; f < 60 * SEC; f++) {
      const c = f % 120, cyc = Math.floor(f / 120), tap = [], hold = [];
      const P = G.P, st = P.st, free = ['idle', 'run', 'land'].includes(P.state);
      if (heavyCycHold(cyc, c, P)) hold.push('heavy');
      else if (c < 78 && P.state !== 'roll') {   // no roll-attacks: the roll carries you through the boss, a rolling swing would whiff
        const heavyCyc = cyc % 3 === 2 && hvCost < G.D.maxSt * 0.6;   // (nobody saves 80% of their breath for the staff's spin mid-fight)
        if (phase === 'art' && didA !== cyc && c < 30 && free && E('cdLeft("art", SAVE.art) <= 0 && !!ARTS[SAVE.art] && P.fp >= Math.round(ARTS[SAVE.art].fp * skArtCostMul())')) { tap.push('art'); arts++; didA = cyc; }
        else if (heavyCyc && didH !== cyc && c < 30) { if (free && st >= hvCost) { tap.push('heavy'); hold.push('heavy'); didH = cyc; heavies++; } }   // every third opening: a charged heavy if it can land before the swing (else lights)
        else if (heavyCyc && P.state === hvTag && !P.charged) hold.push('heavy');   // hold to a full charge
        else if (f % 6 === 0 && st > ltCost + 1 && P.state !== 'art') tap.push('attack');   // swing while a roll stays affordable (a roll needs st > 0)
      }
      if (c === 84 && phase === 'art' && P.fp < 25 && P.flasksB > 0 && free) tap.push('mana');
      if (c === 102 && st > 0) E("hitstop = 0; if (P.state !== 'roll' && P.state !== 'dead') { if (!['idle','run','land'].includes(P.state)) setP('idle', 'idle', true); if (P.st > 0) doRoll(0); }");   // the swing: roll through it (real stamina)
      if (tap.includes('attack') || tap.includes('heavy')) swings++;
      const h0 = b.hp, m0 = acc.melee + acc.sig + acc.status;
      I().step(1, hold, tap);
      const tick = (h0 - b.hp) - (acc.melee + acc.sig + acc.status - m0);   // hp lost outside hit(): burn / rot ticks
      if (tick > 0) { if (b.__burnSig && b._burnT > 0) acc.sig += tick; else acc.status += tick; }
      if (G.P.hp > hp) healed += G.P.hp - hp;
      G.P.hp = G.D.maxHp * 0.5; hp = G.P.hp;
      if (G.state !== 'play') G.step(1, [], ['pause']);
      if (phase === 'far60' || phase === 'farR') { G.P.x = px; G.P.vx = 0; G.P.face = 1; }
      else if (G.P.ground && ['idle', 'run'].includes(G.P.state) && Math.abs(G.P.x - px) > 4) { G.P.x = px; G.P.face = 1; }
      else if (G.P.state !== 'roll' && G.P.x > bx - 12) G.P.x = bx - 12;   // lunges stop at the boss's body instead of carrying you through it
    }
    b.hit = oh;
    const tot = acc.melee + acc.sig + acc.status;
    if (phase === 'near') Object.assign(res, { dps: Math.round(tot / SEC), sig: Math.round(acc.sig / SEC), sigPct: Math.round(acc.sig / Math.max(1, tot) * 100), status: Math.round(acc.status / SEC), statusPct: Math.round(acc.status / Math.max(1, tot) * 100), healPerMin: Math.round(healed / SEC * 60), heavies, presses: swings, reach: Math.round(reach), light: Math.round(G.D.light) });
    else if (phase === 'art') Object.assign(res, { artDps: Math.round(tot / SEC), arts, artHealPerMin: Math.round(healed / SEC * 60) });
    else if (phase === 'far60') res.far60 = Math.round(tot / SEC), res.far60sig = Math.round(acc.sig / SEC);
    else res.farRsig = Math.round(acc.sig / SEC);
  }
  out[id] = res;
}
return out;
