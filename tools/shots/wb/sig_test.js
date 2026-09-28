// signature rules test (agent WB): worst case -- infinite stamina, mashing the combo with a charged heavy every 2 s.
// For every weapon with a signature: signature damage share, the shortest gap between two signature damage bursts,
// and what a plain first light hit adds (only on-hit procs may: glyph, glitch, stoked blade). Reach is bench_real's farR column.
// SHOT_HTML=web/dist/wb.html node tools/shots/shot.js tools/shots/wb/sig_test.js tools/shots/wb/out
await boot(); G.giveArmory(); G.grantTechniques();
const E = G.sk.ev;
E(`(() => {
  if (window.__wbS) return;
  const W = window.__wbS = { ctx: 0, projSig: 0, ms: 0 };
  performance.now = () => W.ms;
  W.step = (n, hold = [], tap = []) => { tap.forEach(press); hold.forEach(a => held.add(a)); for (let i = 0; i < n; i++) { W.ms += 1000 / 60; update(1 / 60); } hold.forEach(release); tap.forEach(release); };
  const tagNew = (nW, nP) => { for (let i = nW; i < WFX.length; i++) wrapE(WFX[i]); for (let i = nP; i < projectiles.length; i++) projectiles[i].__sig = 1; };
  const mark = fn => function (...a) { const nW = WFX.length, nP = projectiles.length; W.ctx++; try { return fn.apply(this, a); } finally { W.ctx--; tagNew(nW, nP); } };
  function wrapE(e) { if (!e || e.__sig) return; e.__sig = 1; if (e.update) e.update = mark(e.update); }
  for (const s of Object.values(SIGS)) for (const k of ['swing', 'finisher', 'hit', 'crit', 'dive', 'block']) { const d = Object.getOwnPropertyDescriptor(s, k); if (d && typeof d.value === 'function') s[k] = mark(d.value); }
  const og = outgoing; outgoing = function (b, m, k, src) { if (src && src.__sig) W.projSig = 1; return og.apply(this, arguments); };
})()`);
const I = () => window.__wbS;
const out = {};
for (const id of E('Object.keys(SIGS)')) {
  { let seed = 99; Math.random = () => (seed = (seed * 16807) % 2147483647) / 2147483647; }
  G.SAVE.weapon = id; G.SAVE.weapons[id] = 5; G.SAVE.lastCls = 'sword';
  G.give({ stats: { vig: 35, mnd: 25, end: 25, str: 30, dex: 30, fth: 25 }, charmsEq: [], skills: [] });
  delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
  G.tp('C5', 6, 10); const b = G.boss;
  for (let i = 0; i < 200 && !b.active; i++) { I().step(4, ['right']); G.P.hp = 99999; if (G.state !== 'play') G.step(1, [], ['pause']); }
  const bx = b.x, by0 = b.y;
  b.update = function (dt) { this.x = bx; this.y = by0; this.commonUpdate(dt); if (this.state === 'stagger') { this.anim.update(dt); this.t -= dt; if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); } } };
  b.state = 'idle'; b.maxHp = 3500; b.hp = 1e7;
  E('refreshDerived(false); P.cds = {}; P.sigCd = {}; hitstop = 0; clearBuffer(); WFX = []; projectiles.length = 0');
  G.P.x = bx - 34; G.P.face = 1;
  let f = 0, sig = 0, all = 0, firstSig = -1, lastBurst = -99, minGap = 99, firstHit = null;
  const reach = G.wb ? G.wb.sigReach() : 0, oh = b.hit;
  b.hit = function (info) {
    const h0 = this.hp, s = I().ctx > 0 || I().projSig; I().projSig = 0;
    const r = oh.call(this, info), d = h0 - this.hp; all += Math.max(0, d);
    if (s && d > 0) { sig += d; const t = f / 60; if (t - lastBurst > 0.5) { if (lastBurst > 0) minGap = Math.min(minGap, t - lastBurst); lastBurst = t; } if (firstSig < 0) firstSig = t; }
    return r;
  };
  // 1) one plain light hit: nothing but on-hit procs (which have their own per-foe cooldowns)
  I().step(1, [], ['attack']); for (let i = 0; i < 40; i++) { f++; I().step(1); }
  firstHit = Math.round(sig);
  // 2) worst case spam for 20 s
  for (; f < 60 * 21; f++) {
    const c = f % 120, tap = [], hold = [];
    G.P.st = 999;
    if (c === 0 || (c < 30 && ['idle', 'run', 'land'].includes(G.P.state) && G.P.state !== E('moveset().heavy') && !G.P._wbH)) { tap.push('heavy'); hold.push('heavy'); G.P._wbH = 1; }
    if (c === 119) G.P._wbH = 0; else if (c < 90 && G.P.state === E('moveset().heavy') && !G.P.charged) hold.push('heavy');
    else if (f % 5 === 0 && c < 80 && G.P.state !== E('moveset().heavy')) tap.push('attack');   // a breath before each heavy so it can start
    I().step(1, hold, tap);
    if (G.state !== 'play') G.step(1, [], ['pause']);
    if (G.P.ground && ['idle', 'run'].includes(G.P.state) && Math.abs(G.P.x - (bx - 34)) > 4) { G.P.x = bx - 34; G.P.face = 1; }
    else if (G.P.state !== 'roll' && G.P.x > bx - 12) G.P.x = bx - 12;
  }
  b.hit = oh;
  out[id] = { firstLightSig: firstHit, sigPctSpam: Math.round(sig / Math.max(1, all) * 100), minGapS: minGap === 99 ? null : +minGap.toFixed(2), reach: Math.round(reach) };
}
return out;
