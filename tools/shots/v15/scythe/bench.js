// v15 Scythe dmg/s bench (tools/shots/wm/bench.js rules). 1) "table": each route looped for SECS against a still target
// (it follows you at `far` px), infinite stamina: damage / AR / s. 2) "boss": Gravetusk held in place swinging every 2 s
// (a 1.3 s opening, then a roll), real stamina, real hitstop, the main combo; souls and Reaps as they come.
const SECS = 12, BSECS = 30;
const ROUTES = [
  ['J J J J (far edge, 38 px)', ['J', 'J', 'J', 'J'], { far: 38 }],
  ['J J J J (close, 24 px)', ['J', 'J', 'J', 'J'], { far: 24 }],
  ['J J J + Reap (souls from the chain)', ['J', 'J', 'J', { b: 'K', hold: 300 }], { far: 38 }],
  ['J J J J + Reap', ['J', 'J', 'J', 'J', { b: 'K', hold: 300 }], { far: 38 }],
  ['IV: J J + Reap (2 souls = full)', ['J', 'J', { b: 'K', hold: 300 }], { far: 38, rank: 4 }],
  ['J J K spiral', ['J', 'J', 'K'], { far: 34 }],
  ['J K hook pull loop', ['J', 'K'], { far: 38 }],
  ['K loop', ['K'], { far: 36, keep: 'P.scySouls = 0' }],
  ['K K loop', ['K', 'K'], { far: 36, keep: 'P.scySouls = 0' }],
  ['charged crescent loop', [{ b: 'K', hold: 800 }], { far: 36, keep: 'P.scySouls = 0' }],
  ['pendulum J J (pause) J J (II)', ['J', 'J', { b: 'wait', ms: 200 }, 'J', 'J'], { far: 36, rank: 2 }],
  ['hook step -> backstab (II)', ['I', 'J'], { far: 30, rank: 2, nofollow: true }],
];
const out = { table: [], boss: [] };
for (const [name, pat, o] of ROUTES) {
  E('MV.scyHarvests = 0');
  W().reset('scythe', o.rank || 1); arena(); W().reset('scythe', o.rank || 1); E('D.maxSt = 1e6; P.st = 1e6; P.scySouls = 0');
  W().dummy(o.far); if (!o.nofollow) E('window.__wm.follow = ' + o.far);
  let i = 0, holdLeft = 0, waitLeft = 0, t0 = null; const N = SECS * 60;
  for (let f = 0; f < N + 900; f++) {
    if (holdLeft > 0 && --holdLeft === 0) W().up('heavy');
    E('P.st = 1e6; if (P.x > 330) P.x -= 200; if (P.x < 60) P.x += 200' + (o.keep ? '; ' + o.keep : ''));
    if (o.nofollow) E(`(() => { const d = enemies.find(e => e.wmDummy); if (d && ['idle','run','land'].includes(P.state)) { P.face = d.x > P.x ? 1 : -1; d.x = P.x + P.face * ${o.far}; } })()`);
    if (waitLeft > 0) { waitLeft--; W().frame(1); continue; }
    const p = pat[i % pat.length], idleOnly = typeof p !== 'string' || p === 'I';   // holds and I start from neutral (I isn't queued mid-move)
    const busy = E('!!ATK[P.state] && !!P.mvQ'), free = E(idleOnly ? "['idle','run','land'].includes(P.state)" : "['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && !ATK[P.state].mv.loop && !(ATK[P.state].mv.fin && ATK[P.state].mv.total - P.mvT > 110))");   // a finisher only takes a new chain's press in its last 120 ms
    if (holdLeft === 0 && free && !busy) {
      if (p.b === 'wait') { if (E("['idle','run','land'].includes(P.state)")) { waitLeft = Math.round(p.ms / (1000 / 60)); i++; } W().frame(1); continue; }
      if (typeof p === 'string') { const k = { J: 'attack', K: 'heavy', I: 'parry' }[p]; W().down(k); W().frame(1); W().up(k); }
      else { W().down('heavy'); holdLeft = Math.round(p.hold / (1000 / 60)); W().frame(1); }
      i++;
      if (t0 === null) { t0 = W().ms; W().log = []; }
      continue;
    }
    W().frame(1);
    if (t0 !== null && W().ms - t0 >= SECS * 1000) break;
  }
  W().up('heavy');
  const secs = (W().ms - t0) / 1000, L = G.D.light, hits = W().log.filter(h => h.melee);
  const tally = {}; for (const h of hits) tally[h.st] = (tally[h.st] || 0) + 1;
  out.table.push({ harvests: E('MV.scyHarvests || 0'), route: name, dps: +(hits.reduce((a, h) => a + h.dmg, 0) / L / secs).toFixed(2), reaps: tally.scy_reap || 0, hits: Object.entries(tally).map(([k, v]) => k + 'x' + v).join(' ') });
}
// ---- boss bench: the main combo (J J J J), and J J J J with Reaps whenever 3 souls are up
for (const mode of ['JJJJ', 'JJJJ+Reap', 'JJJ+Reap']) {
  W().reset('scythe', 1); E('enemies = enemies.filter(e => !e.wmDummy)');
  delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
  G.tp('C5', 6, 10); const b = G.boss;
  for (let i = 0; i < 200 && !b.active; i++) { W().down('right'); W().frame(4); W().up('right'); G.P.hp = 99999; }
  W().reset('scythe', 1); E('enemies = enemies.filter(e => !e.wmDummy); P.scySouls = 0');
  const bx = b.x, by0 = b.y;
  b.update = function (dt) { this.x = bx; this.y = by0; this.commonUpdate(dt); if (this.state === 'stagger') { this.anim.update(dt); this.t -= dt; if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); } } };
  b.state = 'idle'; b.maxHp = 3500; b.hp = 1e7;
  let sum = 0, reaps = 0; const oh = b.hit; b.hit = function (info) { if (info.melee) sum += info.dmg; if (G.P.state === 'scy_reap') reaps++; return oh.call(this, info); };
  const hb = b.hurtbox(), px = hb.x0 - 8 - 30; G.P.x = px; G.P.face = 1;   // the near edge of the (padded) boss box ~30 px out: the far half
  let swings = 0, holdLeft = 0, n = 0;
  for (let f = 0; f < 60 * BSECS; f++) {
    const c = f % 120;
    if (holdLeft > 0 && --holdLeft === 0) W().up('heavy');
    const free = E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && !(ATK[P.state].mv.fin && ATK[P.state].mv.total - P.mvT > 110))");
    if (c < 78 && free && holdLeft === 0 && G.P.st > 12 && G.P.state !== 'roll') {
      const reap = mode !== 'JJJJ' && E('P.scySouls') >= 3 && E("['idle','run','land','scy_3','scy_4'].includes(P.state)") && (mode === 'JJJ+Reap' ? n >= 3 : true);
      if (reap && G.P.st > 18) { W().down('heavy'); holdLeft = 18; W().frame(1); n = 0; }
      else { W().tap('attack'); n++; }
      swings++; continue;
    }
    if (c === 102) E("hitstop = 0; if (P.state !== 'roll' && P.state !== 'dead') { if (!['idle','run','land'].includes(P.state)) setP('idle', 'idle', true); if (P.st > 0) mvDodgeStart(0); }");
    W().frame(1); G.P.hp = G.D.maxHp;
    if (G.P.ground && ['idle', 'run'].includes(G.P.state) && Math.abs(G.P.x - px) > 4) { G.P.x = px; G.P.face = 1; }
  }
  W().up('heavy'); b.hit = oh;
  out.boss.push({ mode, dps: +(sum / G.D.light / BSECS).toFixed(2), presses: swings, reapHits: reaps, harvests: E('MV.scyHarvests || 0') });
  E('MV.scyHarvests = 0');
}
return out;
