// v17 A2 Litany of Fists: balance. (1) one use on the dummy, tapped and held, per style: damage in light-AR units ("hits"),
// hits per FP, hits per cooldown-second, time; (2) the boss bench of tools/shots/v15/fist/bench.js (a held Gravetusk
// swinging every 2 s, a 1.3 s opening, a roll through each swing, real stamina) for the type's routes with and without
// the art used whenever it is ready (real FP: the bar you start with, no flasks), and the art alone (FP refilled) --
// it must not beat the type's best route. SHOT_HTML=$PWD/web/dist/v17_fist.html sh tools/shots/wm/run.sh tools/shots/v17/fist/bench.js
const BSECS = 30, B = { J: 'attack', K: 'heavy', I: 'parry', O: 'art' };
const out = { use: [], boss: [] };
for (const style of ['swift', 'iron']) for (const hold of [false, true]) {
  W().reset('fist', 1); arena(); W().reset('fist', 1); E(`P.ftStyle = '${style}'; P.cds = {}; P.fp = D.maxFp; P.ftPdT = 0`); W().dummy(26); W().log = [];
  const t0 = W().ms; W().down('art'); W().frame(hold ? 50 : 1); W().up('art'); let f = 0; while (E("P.state === 'art'") && f++ < 600) W().frame(1);
  const secs = (W().ms - t0) / 1000, hits = W().log.reduce((a, h) => a + h.dmg, 0) / E('D.light'), A = E('[ARTS.litany.fp, cdBase("art","litany")]');
  out.use.push({ style, hold, hits: +hits.toFixed(2), perFp: +(hits / A[0]).toFixed(3), perCdSec: +(hits / A[1]).toFixed(3), secs: +secs.toFixed(2), poise: W().log.reduce((a, h) => a + h.poise, 0) });
}
const busy = () => E('P.state === "art" || (!!ATK[P.state] && (!!P.mvQ || !!P.ftShiftQ || !!P.ftShiftCarry))');
const free = () => E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && !P.ftShiftQ && !P.ftShiftCarry && P.mvT > 40 && !ATK[P.state].mv.loop)");
const artReady = () => E('cdLeft("art", "litany") <= 0 && P.fp >= ARTS.litany.fp');
for (const [label, style, pat, art] of [['Swift J J J J', 'swift', 'JJJJ', 0], ['Swift J J J J + art', 'swift', 'JJJJ', 1], ['Iron J J J', 'iron', 'JJJ', 0], ['Iron J J J + art', 'iron', 'JJJ', 1],
  ['Shift dance J (J I)', 'swift', 'JJIJIJIJI', 0], ['Shift dance + art', 'swift', 'JJIJIJIJI', 1], ['Swift art only (FP refilled)', 'swift', '', 2], ['Iron art only (FP refilled)', 'iron', '', 2]]) {
  W().reset('fist', 1); E('enemies = enemies.filter(e => !e.wmDummy)');
  delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
  G.tp('C5', 6, 10); const b = G.boss;
  for (let i = 0; i < 200 && !b.active; i++) { W().down('right'); W().frame(4); W().up('right'); G.P.hp = 99999; }
  W().reset('fist', 1); E(`enemies = enemies.filter(e => !e.wmDummy); P.ftStyle = '${style}'; P.ftFlow = 0; P.cds = {}; P.fp = D.maxFp`);
  const bx = b.x, by0 = b.y;
  b.update = function (dt) { this.x = bx; this.y = by0; this.commonUpdate(dt); if (this.state === 'stagger') { this.anim.update(dt); this.t -= dt; if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); } } };
  b.state = 'idle'; b.maxHp = 3500; b.hp = 1e7;
  let sum = 0, artSum = 0; const oh = b.hit; b.hit = function (info) { if (info.melee) { sum += info.dmg; if (G.P.state === 'art' || E('LT_FX.some(f => f.kind === "wave" && !f.done)')) artSum += info.dmg; } return oh.call(this, info); };
  const px = bx - 30; G.P.x = px; G.P.face = 1;
  let k = 0, presses = 0, uses = 0;
  for (let f = 0; f < 60 * BSECS; f++) {
    const c = f % 120;
    if (c === 0) { k = 0; if (G.P.state !== 'art') E(`P.ftStyle = '${style}'`); }
    if (art === 2) E('P.fp = D.maxFp');
    if (c < 78 && G.P.state !== 'roll' && !busy() && k < 99) {
      if (art && c < 40 && E("['idle','run','land'].includes(P.state)") && artReady()) { W().tap('art', 1); uses++; continue; }
      if (art !== 2 && pat) { const p = pat[k % pat.length], ok = p === 'I' ? E('!!ATK[P.state]') : free();
        if (ok && G.P.st > 8) { W().tap(B[p], 1); k++; presses++; continue; } }
    }
    if (c === 102) E("hitstop = 0; P.mvQ = null; P.ftShiftQ = null; if (P.state !== 'roll' && P.state !== 'dead') { if (!['idle','run','land'].includes(P.state)) setP('idle', 'idle', true); if (P.st > 0) mvDodgeStart(0); }");
    W().frame(1); G.P.hp = G.D.maxHp;
    if (G.P.ground && ['idle', 'run'].includes(G.P.state) && Math.abs(G.P.x - px) > 4) { G.P.x = px; G.P.face = 1; }
    else if (G.P.state !== 'roll' && G.P.state !== 'art' && G.P.x > bx - 12) G.P.x = bx - 12;
  }
  b.hit = oh;
  out.boss.push({ route: label, dps: +(sum / G.D.light / BSECS).toFixed(2), artShare: +(artSum / Math.max(1, sum)).toFixed(2), uses, presses });
}
return out;
