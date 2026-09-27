// walk every SC edge connection both ways (horizontal: hold a direction; vertical: jump up / drop through)
await boot(); G.grantTechniques(); G.SETTINGS.god = 1; Object.assign(G.SAVE.items, { talon: 1, wings: 1, moonstep: 1 }); G.SAVE.flags['boss:oswin'] = 1; G.SAVE.flags['sc:seal'] = 1;
const out = [];
const walk = (from, x, y, dir, to, frames = 240) => {
  G.tp(from, x, y); G.step(10); const k = dir > 0 ? 'right' : 'left';
  for (let i = 0; i < frames && G.room === from; i++) G.step(1, [k], (i % 24 === 12) ? ['jump'] : []);
  const r1 = G.room; G.step(15);
  const k2 = dir > 0 ? 'left' : 'right';
  for (let i = 0; i < frames && G.room === r1; i++) G.step(1, [k2], (i % 24 === 12) ? ['jump'] : []);
  out.push(`${from} ${dir > 0 ? '→' : '←'} ${r1}${r1 === to ? '' : ' (WANTED ' + to + ')'} ← back: ${G.room}`);
};
walk('SF10', 3, 11, -1, 'SF16'); walk('SF10', 52, 11, 1, 'SF13'); walk('SF13', 51, 6, 1, 'SF11');
walk('SF14', 3, 7, -1, 'SF12'); walk('SF12', 3, 17, -1, 'SF15');
walk('NH9', 3, 12, -1, 'NH13'); walk('NH9', 44, 12, 1, 'NH10'); walk('NH10', 44, 10, 1, 'NH8');
walk('NH8', 3, 39, -1, 'NH14'); walk('NH8', 44, 42, 1, 'NH11'); walk('NH11', 92, 14, 1, 'NH16'); walk('NH12', 3, 24, -1, 'NH15');
walk('E5', 3, 27, -1, 'E7'); walk('H1', 3, 10, -1, 'H2'); walk('H2', 3, 10, -1, 'H3');
// vertical: up the shafts (stand under, jump / wall-jump), then drop back through the grate
const up = (from, x, y, to) => {
  G.tp(from, x, y); G.step(10);
  for (let i = 0; i < 300 && G.room === from; i++) { if (G.P.state === 'wall') G.step(1, ['jump'], ['jump']); else G.step(1, ['jump', i % 40 < 20 ? 'left' : 'right'], (i % 16 === 0) ? ['jump'] : []); }
  const r1 = G.room; G.step(30);
  for (let i = 0; i < 200 && G.room === r1; i++) G.step(1, ['down'], (i % 10 === 0) ? ['jump'] : []);
  out.push(`${from} ↑ ${r1}${r1 === to ? '' : ' (WANTED ' + to + ')'} ↓ back: ${G.room}`);
};
up('SF11', 41, 3, 'SF14'); up('SF14', 31, 2, 'SF18'); up('NH8', 35, 3, 'NH4'); up('NH11', 70, 2, 'NH12'); up('NH12', 2, 2, 'NH6'); up('E5', 51, 3, 'E4');
return out;
