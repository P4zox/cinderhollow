await boot(); window.__godS = true;
G.give({ items: { wings: 1, talon: 1 }, stats: { vig: 30, mnd: 15, end: 25, str: 22, dex: 18, fth: 10 } });
G.SAVE.seenAreas = { starfall: 1, crown: 1 };
G.tp('SF4', 18, 12); S(40); await snap('s0_sf4_shrine');
G.tp('SF6', 18, 48); S(40); await snap('s1_sf6_shrine');
G.tp('SF7', 5, 16); S(10);
for (let i = 0; i < 120 && G.state !== 'cut'; i++) S(2, ['right']);
for (let i = 0; i < 14 && G.state === 'cut'; i++) { S(22); await snap('s2_cut' + String(i).padStart(2, '0')); }
for (let i = 0; i < 60 && G.state === 'cut'; i++) S(1, [], ['pause']);
const b = G.boss; let k = 0;
for (let i = 0; i < 700; i++) {
  const d = Math.abs(b.x - G.P.x), to = b.x < G.P.x ? 'left' : 'right';
  S(2, d > 40 ? [to] : [], d <= 40 && i % 7 === 0 ? ['attack'] : []);
  if (i % 50 === 0 && k < 12) await snap('s3_fight' + String(k++).padStart(2, '0'));
}
return 'ok';
