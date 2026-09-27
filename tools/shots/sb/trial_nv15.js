G.SAVE.items.emberdash = 1; G.tp('NV15', 51, 12); for (let i = 0; i < 6; i++) { G.step(20); settle(); }
TR.done0 = S.SYS.result; TR.room = 'NV15'; TR.home = [51 * 16 + 8, 51, 12];
const P = () => G.P;
const onFloor = (x0, x1, y) => P().ground && P().x > x0 && P().x < x1 && Math.abs(P().y - y) < 1;
const acts = [[['left'], []], [['left', 'jump'], ['jump']], [[], []], [['left'], ['roll']], [['right'], []], [['jump'], ['jump']]];
let plan = TR.dfs([], () => onFloor(368, 386, 208), acts, 4, 90, 6000);
if (!plan) return TR.log;
plan = TR.search(plan, () => onFloor(290, 352, 208), -1, 300, { gen: () => { const s = []; const w = Math.floor(Math.random() * 12); for (let i = 0; i < w; i++) s.push([[], []]); s.push([['left'], ['roll']]); for (let i = 0; i < 60; i++) s.push([Math.random() < 0.5 ? ['left'] : [], []]); return s; } });
if (!plan) return TR.log;
const climb = () => { let side = -1, tap = 0, ph = 0;
  return i => {
    const p = P(); const L = side < 0 ? 'left' : 'right';
    if (ph === 0) { if (p.x > 283) return [['left'], []]; ph = 1; return [['left', 'jump'], ['jump']]; }
    if (p.y < 60) return [['left'], []];
    if (p.state === 'wall' && tap <= 0) { side = -side; tap = 8; return [[side < 0 ? 'left' : 'right', 'jump'], ['jump']]; }
    tap--; return [p.vy < 0 ? [L, 'jump'] : [L], []];
  }; };
let got = null;
for (let t = 0; t < 40 && !got; t++) {
  const w = t % 10, f = climb();
  const r = TR.run(plan, () => onFloor(16, 190, 64), { fn: i => i < w ? [[], []] : f(i - w), max: 400 });
  if (r.ok) got = plan.concat(r.rec);
}
TR.log.push('climb ' + !!got); if (!got) return TR.log; plan = got;
TR.run(plan, () => false, { fn: i => [['left'], []], max: 200 });
TR.log.push('result ' + JSON.stringify(S.SYS.result && { t: S.SYS.result.time, gold: S.SYS.result.gold, first: S.SYS.result.first }) + ' plan frames ' + plan.length);
for (let i = 0; i < 260; i++) G.step(1);
TR.log.push('charm ' + G.SAVE.charms.includes('c_x3_hood'));
await snap('nv15_done');
return { log: TR.log, plan: plan.map(f => (f[0].join('+') || '_') + (f[1].length ? '!' + f[1].join('+') : '')).join(' ') };
