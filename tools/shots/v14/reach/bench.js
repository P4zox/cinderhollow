// v14 reach bench: (1) table routes (dmg/s in light AR, dummy that follows, infinite stamina -- tools/shots/wm/bench.js rules)
// (2) a real boss: Gravetusk (C5) with its own AI, a scripted player that dodges its swings and fights at the weapon's
//     range for BOSS_SECS; real stamina. Reports dmg/s dealt and hits taken.
const SECS = window.__wmSecs || 12, BSECS = window.__bossSecs || 40;
const KEY = { J: 'attack', K: 'heavy', L: 'roll', I: 'parry' };
const ROUTES = [
  ['staff', 1, 'J J J J', ['J', 'J', 'J', 'J']],
  ['staff', 1, 'K spin loop', ['K']],
  ['staff', 1, 'J J K (launcher) + air J', ['J', 'J', 'K', 'J']],
  ['whip', 1, 'J J J untipped', ['J', 'J', 'J'], { far: 22 }],
  ['whip', 1, 'J J J tipped', ['J', 'J', 'J'], { far: 70 }],
  ['whip', 1, 'J J K tipped (trip lash)', ['J', 'J', 'K'], { far: 70, keep: 'P.crack = 0' }],
  ['whip', 1, 'tipped K loop', ['K'], { far: 70, keep: 'P.crack = 0' }],
  ['whip', 1, 'tipped K loop + thunderclaps', ['K'], { far: 70 }],
  ['whip', 1, 'close K loop + thunderclaps', ['K'], { far: 24 }],
  ['whip', 1, 'L K coil loop (close)', ['L', 'K'], { far: 30 }],
];
const out = { table: [], boss: [] };
for (const [type, rank, name, pat, o = {}] of (window.__noTable ? [] : ROUTES)) {
  W().reset(type, rank); arena(); W().reset(type, rank); E('D.maxSt = 1e6; P.st = 1e6; P.momLand = null');
  W().dummy(o.far || 26); E('window.__wm.follow = ' + (o.far || 26));
  let i = 0, t0 = null;
  for (let f = 0; f < SECS * 60 + 600; f++) {
    E('P.st = 1e6; if (P.x > 330) P.x -= 200' + (o.keep ? '; ' + o.keep : ''));
    const free = E("['idle','run','land','air'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && !ATK[P.state].mv.loop) || (P.state === 'roll' && P.dg && P.dg.t > 200)");
    if (free) { const b = KEY[pat[i % pat.length]]; W().down(b); W().frame(1); W().up(b); i++; if (t0 === null) { t0 = W().ms; W().log = []; } continue; }
    W().frame(1);
    if (t0 !== null && W().ms - t0 >= SECS * 1000) break;
  }
  const secs = (W().ms - t0) / 1000, dmg = W().log.filter(h => h.melee).reduce((a, h) => a + h.dmg, 0) / G.D.light;
  const tally = {}; for (const h of W().log.filter(h => h.melee)) tally[h.st] = (tally[h.st] || 0) + 1;
  out.table.push(`${type} ${name}: ${(dmg / secs).toFixed(2)}/s  [${Object.entries(tally).map(([k, v]) => k + 'x' + v).join(' ')}]`);
}
// ---- the real boss
const PLANS = {
  staff_ground: { type: 'staff', range: [8, 22], pat: ['J', 'J', 'J', 'J'] },
  staff_vault: { type: 'staff', range: [10, 26], pat: ['I', 'J', 'K', 'dJ'] },
  whip_tip: { type: 'whip', range: [58, 74], pat: ['J', 'J', 'K'] },
  whip_close: { type: 'whip', range: [6, 22], pat: ['J', 'J', 'J'] },
  whip_coil: { type: 'whip', range: [6, 22], pat: ['L', 'K', 'J'] },
  ref_longsword: { type: 'longsword', range: [8, 22], pat: ['J', 'J', 'J', 'J'] },
  ref_spear: { type: 'spear', range: [20, 34], pat: ['J', 'J', 'J'] },
};
if (window.__plans) for (const k of Object.keys(PLANS)) if (!window.__plans.includes(k)) delete PLANS[k];
for (const [plan, pl] of Object.entries(PLANS)) try {
  W().reset(pl.type, 1); E('enemies = enemies.filter(e => !e.wmDummy)');
  delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
  G.tp('C5', 6, 10); const b = G.boss;
  for (let i = 0; i < 200 && !b.active; i++) { W().down('right'); W().frame(4); W().up('right'); G.P.hp = 99999; }
  W().reset(pl.type, 1); E('enemies = enemies.filter(e => !e.wmDummy); P.momLand = null');
  b.maxHp = 1e7; b.hp = 1e7;
  let sum = 0; const oh = b.hit; b.hit = function (info) { if (info.melee) sum += info.dmg; return oh.call(this, info); };
  let taken = 0, lastHp = G.P.hp, dodged = null, i = 0, rolls = 0, outSt = 0;
  for (let f = 0; f < 60 * BSECS; f++) {
    const p = G.P, h0 = b.hurtbox && b.hurtbox(), hb = h0 ? [h0.x0 - 8, h0.x1 + 8] : [b.x - 20, b.x + 20];
    const dir = (hb[0] + hb[1]) / 2 > p.x ? 1 : -1, near = dir > 0 ? hb[0] - p.x : p.x - hb[1];
    const atk = b.state === 'attack' || b.state === 'windup', key = b.atk + ':' + (b.atkId || 0) + ':' + Math.floor(f / 90);
    const free = E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && !ATK[P.state].mv.loop)");
    for (const a of ['left', 'right']) W().up(a);
    if (atk && near < 110 && dodged !== key && p.st > 10 && ['idle', 'run', 'land'].includes(p.state) || (atk && near < 110 && dodged !== key && E('!!ATK[P.state] && P.mvT >= ATK[P.state].mv.wind'))) {
      dodged = key; W().down(dir > 0 ? 'left' : 'right'); W().tap('roll'); rolls++; continue;
    }
    if (['idle', 'run', 'land'].includes(p.state) && (near < pl.range[0] || near > pl.range[1])) { W().down(near > pl.range[1] ? (dir > 0 ? 'right' : 'left') : (dir > 0 ? 'left' : 'right')); W().frame(1); continue; }
    if (free && p.st > 12) {
      G.P.face = dir; const s = pl.pat[i % pl.pat.length]; i++;
      if (s === 'dJ') { for (let k = 0; k < 30 && !G.P.ground && E('!!ATK[P.state]'); k++) W().frame(1); W().down('down'); W().tap('attack'); W().up('down'); }
      else W().tap(KEY[s]);
      continue;
    }
    if (free && p.st <= 12) outSt++;
    W().frame(1);
    if (G.P.hp < lastHp) taken++; G.P.hp = 99999; lastHp = G.P.hp; if (G.P.state === 'dead') G.P.state = 'idle';
  }
  b.hit = oh;
  out.boss.push(`${plan}: ${(sum / G.D.light / BSECS).toFixed(2)} dmg/s, hits taken ${taken}, rolls ${rolls}, stamina-starved frames ${outSt}`);
} catch (e) { out.boss.push(plan + ' EXC ' + e.message); }
return out;
