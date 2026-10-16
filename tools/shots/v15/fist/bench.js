// v15 Martial Arts bench (WM prelude): dmg/s per route on the dummy (infinite stamina, real inputs), in light-AR units
// (x1 = one Longsword light a second), plus the boss bench (wm/bench.js rules: a held Gravetusk swinging every 2 s,
// real stamina, a roll through each swing). SHOT_HTML=web/dist/v15_fist.html sh tools/shots/wm/run.sh tools/shots/v15/fist/bench.js
const SECS = 12, BSECS = 30;
const B = { J: 'attack', K: 'heavy', I: 'parry' };
// [name, rank, style, prefix presses, cycled presses, target note]; {K: ms} holds K; 'I' is a mid-move Shift
const ROUTES = [
  ['Swift J J J J (main loop)', 1, 'swift', [], ['J', 'J', 'J', 'J'], '2.4-2.8'],
  ['Iron J J J', 1, 'iron', [], ['J', 'J', 'J'], 'alt'],
  ['Swift K K', 1, 'swift', [], ['K', 'K', 'swift'], 'alt'],
  ['Swift J K', 1, 'swift', [], ['J', 'K', 'swift'], 'alt'],
  ['Swift J J K', 1, 'swift', [], ['J', 'J', 'K', 'swift'], 'alt'],
  ['Swift K J J J (snap into the chain)', 1, 'swift', [], ['K', 'J', 'J', 'J', 'swift'], 'alt'],
  ['Iron K K', 1, 'iron', [], ['K', 'K', 'iron'], 'alt'],
  ['Iron J K (throw)', 1, 'iron', [], ['J', 'K', 'iron'], 'alt'],
  ['Iron J J K (pillar)', 1, 'iron', [], ['J', 'J', 'K', 'iron'], 'alt'],
  ['Iron hold K lv2 loop', 1, 'iron', [], [{ K: 1000 }], 'alt (hold time counted)'],
  ['Hundred fists (hold 2 s)', 2, 'swift', [], [{ K: 2000 }], 'alt'],
  ['Shift dance: J, then (J I) x n', 1, 'swift', ['J'], ['J', 'I'], 'the skill loop (top of band)'],
  ['Swift J J -> I -> J J (fstar into elbow, shoulder)', 1, 'swift', [], ['J', 'J', 'I', 'J', 'J', 'swift'], 'alt'],
  ['Iron J -> I -> J J J (wind cut into the Swift chain)', 1, 'iron', [], ['J', 'I', 'J', 'J', 'J', 'iron'], 'alt'],
  ['Tempest: J J J -> I -> K', 3, 'swift', [], ['J', 'J', 'J', 'I', 'K', 'swift'], 'alt'],
  // with the perfect-dodge Focus buff kept up (+10% dmg, +6 px reach)
  ['FOCUS Swift J J J J', 1, 'swift', [], ['J', 'J', 'J', 'J'], '<= ~10% over the band', true],
  ['FOCUS Iron J J J', 1, 'iron', [], ['J', 'J', 'J'], '', true],
  ['FOCUS Shift dance', 1, 'swift', ['J'], ['J', 'I'], '', true],
];
const out = { table: [], boss: [] };
const busy = () => E('!!ATK[P.state] && (!!P.mvQ || !!P.ftShiftQ || !!P.ftShiftCarry)');
const free = () => E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && !P.ftShiftQ && !P.ftShiftCarry && P.mvT > 40 && !ATK[P.state].mv.loop)");
for (const [name, rank, style, pre, cyc, note, focus] of ROUTES) {
  W().reset('fist', rank); arena(); W().reset('fist', rank); E(`D.maxSt = 1e6; P.st = 1e6; P.ftStyle = '${style}'; P.ftFlow = 0; P.inv = 0`);
  W().dummy(24); E('window.__wm.follow = 24');
  const seq = [...pre]; let i = 0, t0 = null, holdLeft = 0;
  const next = () => (i < seq.length ? seq[i] : cyc[(i - seq.length) % cyc.length]);
  for (let f = 0; f < SECS * 60 + 900; f++) {
    E(`P.st = 1e6; P.ftFlow = 0; P.ftPdT = ${focus ? 6 : 0}; if (P.x > 330) P.x -= 200`);
    if (holdLeft > 0) { if (--holdLeft === 0) W().up('heavy'); W().frame(1); continue; }
    let p = next();
    if (p === 'swift' || p === 'iron') {   // wait for neutral, then reset the style (a route that crossed styles starts over)
      if (E("['idle','run','land'].includes(P.state)")) { E(`P.ftStyle = '${p}'`); i++; }
      W().frame(1); continue;
    }
    if (!busy() && (p === 'I' ? E('!!ATK[P.state]') || E('!!P.mvChain') : free())) {
      if (typeof p === 'object') { W().down('heavy'); holdLeft = Math.round(p.K / (1000 / 60)); }
      else W().tap(B[p], 1);
      i++; if (t0 === null) { t0 = W().ms; W().log = []; }
      continue;
    }
    W().frame(1);
    if (t0 !== null && W().ms - t0 >= SECS * 1000) break;
  }
  W().up('heavy');
  const secs = (W().ms - t0) / 1000, L = G.D.light;
  const dmg = W().log.filter(h => h.melee).reduce((a, h) => a + h.dmg, 0) / L;
  const tally = {}; for (const h of W().log.filter(h => h.melee)) tally[h.st] = (tally[h.st] || 0) + 1;
  out.table.push({ route: name, rank, dps: +(dmg / secs).toFixed(2), note, hits: Object.entries(tally).map(([k, v]) => k + 'x' + v).join(' ') });
}
// ---- the boss bench
for (const [label, style, pat] of [['Swift J J J J', 'swift', 'JJJJ'], ['Iron J J J', 'iron', 'JJJ'], ['Shift dance J (J I)', 'swift', 'JJIJIJIJI']]) {
  W().reset('fist', 1); E('enemies = enemies.filter(e => !e.wmDummy)');
  delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
  G.tp('C5', 6, 10); const b = G.boss;
  for (let i = 0; i < 200 && !b.active; i++) { W().down('right'); W().frame(4); W().up('right'); G.P.hp = 99999; }
  W().reset('fist', 1); E(`enemies = enemies.filter(e => !e.wmDummy); P.ftStyle = '${style}'; P.ftFlow = 0`);
  const bx = b.x, by0 = b.y;
  b.update = function (dt) { this.x = bx; this.y = by0; this.commonUpdate(dt); if (this.state === 'stagger') { this.anim.update(dt); this.t -= dt; if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); } } };
  b.state = 'idle'; b.maxHp = 3500; b.hp = 1e7;
  let sum = 0; const oh = b.hit; b.hit = function (info) { if (info.melee) sum += info.dmg; return oh.call(this, info); };
  const px = bx - 30; G.P.x = px; G.P.face = 1;
  let k = 0, presses = 0;
  for (let f = 0; f < 60 * BSECS; f++) {
    const c = f % 120;
    if (c === 0) { k = 0; E(`P.ftStyle = '${style}'`); }
    if (c < 78 && G.P.state !== 'roll' && !busy() && k < 99) {
      const p = pat[k % pat.length], ok = p === 'I' ? E('!!ATK[P.state]') : free();
      if (ok && G.P.st > 8) { W().tap(B[p], 1); k++; presses++; continue; }
    }
    if (c === 102) E("hitstop = 0; P.mvQ = null; P.ftShiftQ = null; if (P.state !== 'roll' && P.state !== 'dead') { if (!['idle','run','land'].includes(P.state)) setP('idle', 'idle', true); if (P.st > 0) mvDodgeStart(0); }");
    W().frame(1); G.P.hp = G.D.maxHp;
    if (G.P.ground && ['idle', 'run'].includes(G.P.state) && Math.abs(G.P.x - px) > 4) { G.P.x = px; G.P.face = 1; }
    else if (G.P.state !== 'roll' && G.P.x > bx - 12) G.P.x = bx - 12;
  }
  b.hit = oh;
  out.boss.push({ route: label, dps: +(sum / G.D.light / BSECS).toFixed(2), presses });
}
return out;
