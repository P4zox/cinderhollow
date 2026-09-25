await boot(); const out = [];
for (const [r, k] of [['C5','hound'],['K4','omen'],['M5','kalden'],['X5','sovereign']]) {
  delete G.SAVE.flags['cut:'+k]; delete G.SAVE.flags['boss:'+k];
  G.tp(r, 6, 11); G.P.hp = 99999; let n = 0;
  for (let i = 0; i < 120 && G.state !== 'cut'; i++) G.step(5, ['right']);
  out.push(k + ' start ' + G.state + ' room ' + G.room + ' boss ' + (G.boss && G.boss.kind));
  while (G.state === 'cut' && n < 50) { G.step(12); if (n % 2 === 0) await snap(k + '_' + String(n).padStart(2,'0')); n++; }
  G.P.hp = 99999; G.step(20); await snap(k + '_zz');
  const b = G.boss; out.push(k + ' end ' + G.state + ' n' + n + (b ? ' boss ' + b.state + ' active ' + b.active + ' y ' + Math.round(b.y) + '/' + b.floor : ' NO BOSS'));
}
return out;
