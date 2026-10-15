// v15 cores bench: every Core's trait measured on the WM dummy (no stamina limit, deterministic rand).
// Run: SHOT_HTML=web/dist/v15_cores.html sh tools/shots/wm/run.sh tools/shots/v15/cores/bench.js <out>
// A cycle = Longsword J J J J (the 4th is the finisher, attack4) then K (the neutral heavy) then a breath; CYCLES cycles,
// then 5 s for delayed procs and DoTs to land. "bonus" = (enchanted total - plain total) / plain damage of the eligible
// moves: the effective gain ON THE MOVES THE ENCHANT TOUCHES (target +8..15%). Run against a small foe and a great one.
// Also checks: a light-only route never procs (eligibility), and a few utilities (stamina, FP, heals, slows ...).
const CYCLES = 6, R = [], T = (name, pass, detail = '') => R.push(`${pass ? 'OK ' : 'BAD'} ${name}${detail ? '  [' + detail + ']' : ''}`);
const C = G.cores;
const fr = n => W().frame(n);
const tap = (a) => { W().down(a); fr(1); W().up(a); };
const endMove = () => { const s = G.P.state; for (let i = 0; i < 90 && G.P.state === s; i++) fr(1); };
function cycle() { tap('attack'); fr(12); tap('attack'); fr(14); tap('attack'); fr(14); tap('attack'); endMove(); fr(8); tap('heavy'); endMove(); fr(40); }
function setup(kind, great) {
  W().reset('longsword', 5); arena(); W().reset('longsword', 5);
  E('D.maxSt = 1e6; P.st = 1e6; D.maxFp = Math.max(D.maxFp, 60); P.fp = 0; P.lastHit = null; P._crHurtT = -99; P.hp = D.maxHp');
  C.ev(`SAVE.cores = {}; for (const k of Object.keys(CORES)) SAVE.cores[k] = 1; SAVE.enchants = {}; ${kind ? `SAVE.enchants.longsword = '${kind}';` : ''}
    CR.cd = {}; CR.reso = { n: 0, t: -9 }; CR.kindle = 0; CR.kindleT = -9; CR.kindleMv = -1; CR.twin = 0; CR.bell = 0; CR.star = 0; CR.u = {}; CR.procs = 0; CR.dealt = 0; CR.vfx = []; MV.later = []`);
  const d = W().dummy(26, great ? { boss: true } : {});
  W().follow = 26;
  return d;
}
function run(kind, great, route = cycle, n = CYCLES) {
  setup(kind, great);
  for (let i = 0; i < n; i++) route();
  fr(300);
  const L = W().log, tot = L.reduce((s, h) => s + h.dmg, 0);
  const elig = L.filter(h => C.ev(`crElig(ATK['${h.st}'])`) && h.melee).reduce((s, h) => s + h.dmg, 0);
  return { tot, elig, n: L.length, u: C.ev('CR.u'), procs: C.ev('CR.procs || 0'), st: E('P.st'), fp: E('P.fp') };
}
const out = { small: {}, great: {} };
const base = { small: run(null, false), great: run(null, true) };
out.base = { small: [Math.round(base.small.tot), Math.round(base.small.elig)], great: [Math.round(base.great.tot), Math.round(base.great.elig)] };
const pct = (e, b) => Math.round((e.tot - b.tot) / b.elig * 1000) / 10;
for (const k of C.ev('crOrder()')) {
  for (const sz of ['small', 'great']) {
    const e = run(k, sz === 'great');
    out[sz][k] = { bonus: pct(e, base[sz]), u: e.u };
  }
}
// the table, and the gates: no Core's damage bonus may exceed +16% on the eligible moves (unconditional case)
const rows = [];
for (const k of C.ev('crOrder()')) {
  const s = out.small[k], gr = out.great[k], u = Object.entries(gr.u || {}).map(([a, b]) => `${a} ${Math.round(b * 10) / 10}`).join(', ');
  rows.push(`${k.padEnd(13)} small ${String(s.bonus).padStart(5)}%  great ${String(gr.bonus).padStart(5)}%  ${u}`);
  T(`${k}: bonus within budget (<= 16% on eligible moves)`, s.bonus <= 16 && gr.bonus <= 16, `${s.bonus}% / ${gr.bonus}%`);
}
// eligibility: a light-only route (J, pause, J ...) never gains a thing
{ const light = () => { tap('attack'); endMove(); fr(30); };
  const b = run(null, true, light, 10), e = run('overseer', true, light, 10), e2 = run('warden', true, light, 10);
  T('light attacks never carry the enchant (fire DoT)', Math.abs(e.tot - b.tot) < 0.5 && e.procs === 0, `${Math.round(b.tot)} vs ${Math.round(e.tot)}, procs ${e.procs}`);
  T('light attacks never carry the enchant (edge)', Math.abs(e2.tot - b.tot) < 0.5, `${Math.round(b.tot)} vs ${Math.round(e2.tot)}`); }
// conditionals
{ setup('executioners', true); const d = E("enemies.find(e => e.wmDummy)"); E("(() => { const d = enemies.find(e => e.wmDummy); d.maxHp = 1000; d.hp = 200; })()"); cycle(); fr(200);
  const L = W().log, f = L.find(h => h.st === 'attack4');
  setup(null, true); E("(() => { const d = enemies.find(e => e.wmDummy); d.maxHp = 1000; d.hp = 200; })()"); cycle(); fr(200); const f0 = W().log.find(h => h.st === 'attack4');
  T('Verdict: +28% on a finisher against a foe under 30%', f && f0 && Math.abs(f.dmg / f0.dmg - 1.28) < 0.01, f && f0 ? (f.dmg / f0.dmg).toFixed(3) : '-'); }
{ setup('venn', true); E('P.hp = D.maxHp * 0.3'); cycle(); const f = W().log.find(h => h.st === 'attack4'); setup(null, true); cycle(); const f0 = W().log.find(h => h.st === 'attack4');
  T('Last Flame: +16% below 40% HP', f && f0 && Math.abs(f.dmg / f0.dmg - 1.16) < 0.01, f && f0 ? (f.dmg / f0.dmg).toFixed(3) : '-'); }
{ setup('champion', true); E('P._crHurtT = 1e9'); cycle(); const f = W().log.find(h => h.st === 'attack4'); setup(null, true); cycle(); const f0 = W().log.find(h => h.st === 'attack4');
  T('Unyielding: +4% just after being hit', f && f0 && Math.abs(f.dmg / f0.dmg - 1.04) < 0.01, f && f0 ? (f.dmg / f0.dmg).toFixed(3) : '-'); }
// stance cores raise poise on eligible moves only
{ setup('warden', true); cycle(); const L = W().log; setup(null, true); cycle(); const L0 = W().log;
  const p = id => (L.find(h => h.st === id) || {}).poise, p0 = id => (L0.find(h => h.st === id) || {}).poise;
  T('Antler’s Weight: finisher poise x1.25, light poise unchanged', Math.abs(p('attack4') / p0('attack4') - 1.25) < 0.01 && p('attack1') === p0('attack1'), `${p('attack4')} vs ${p0('attack4')}, light ${p('attack1')} vs ${p0('attack1')}`); }
// control effects: great foes resist (duration shrinks with repeats)
{ const s = C.ev(`(() => { const t = { update() {}, x: 0, y: 0 }; P.clk = 100; crSlow(t, 0.85, 2); const a = t._crSlowT, fa = t._crSlowF;
    const b = { update() {}, x: 0, y: 0, boss: true }; crSlow(b, 0.85, 2); const b1 = b._crSlowT, fb = b._crSlowF; b._crSlowT = 0; crSlow(b, 0.85, 2); const b2 = b._crSlowT; b._crSlowT = 0; crSlow(b, 0.85, 2); const b3 = b._crSlowT; b._crSlowT = 0; crSlow(b, 0.85, 2); const b4 = b._crSlowT;
    return [a, fa, b1, fb, b2, b3, b4]; })()`);
  T('Chill: small foe 15% for 2 s; great foe 6%, 1 s, then 0.5, 0.25, 0.25 s', s[0] === 2 && Math.abs(s[1] - 0.85) < 1e-6 && Math.abs(s[2] - 1) < 1e-6 && Math.abs(s[3] - 0.94) < 1e-6 && Math.abs(s[4] - 0.5) < 1e-6 && Math.abs(s[5] - 0.25) < 1e-6 && Math.abs(s[6] - 0.25) < 1e-6, s.map(v => Math.round(v * 1000) / 1000).join(' ')); }
// the Training Grounds row: ◂ ▸ cycles every Core (and none) on the weapon in hand
{ const r = C.ev(`(() => { SAVE.enchants = {}; const R = []; wmTrainingRows(R, () => {}); const row = R.find(q => q && q.label === 'Boss Core'); if (!row) return null;
    const a = row.val(); row.lr(1); const b = row.val(); row.lr(-1); const c = row.val(); row.lr(-1); const d = row.val(); return [a, b, c, d]; })()`);
  T('Training Grounds: a Boss Core row cycles the Cores', r && r[0] === 'none' && r[1] === 'Rend' && r[2] === 'none' && r[3] !== 'none', JSON.stringify(r)); }
return { results: R, table: rows, base: out.base };
