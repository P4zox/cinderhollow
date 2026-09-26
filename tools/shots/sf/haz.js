await boot(); window.__godS = true;
G.give({ items: { wings: 1, talon: 1 }, stats: { vig: 30, mnd: 15, end: 25, str: 22, dex: 18, fth: 10 } });
G.SAVE.flags['cut:astrel'] = 1; G.SAVE.flags['cutp2:astrel'] = 1;
G.tp('SF7', 12, 16); S(10);
for (let i = 0; i < 200 && !(G.boss && G.boss.active); i++) S(2, ['right']);
const b = G.boss; S(160);
b.hp = Math.round(b.maxHp * 0.45); S(30);
const shots = [];
const pose = async (n) => { b.state = 'idle'; b.cool = 99; S(1); };
for (const c of ['hunter', 'serpent', 'crown']) {
  b.cons = c; b.consT = 30; b.rotT = 0; b.hazT = 0; window.__sf.SFSKY.focus = c; S(1);
  for (let i = 0; i < 4; i++) { S(20); await snap(`h_${c}_${i}`); }
}
await pose(); b.startCast('rain'); S(55); await snap('h_rain'); S(30); await snap('h_rain2');
await pose(); b.startCast('well'); S(70); await snap('h_well');
await pose(); b.startDash(); S(26); await snap('h_dash'); S(20); await snap('h_dash2');
await pose(); b.start('leap'); S(40); await snap('h_leap'); S(22); await snap('h_leap2');
return 'ok';
