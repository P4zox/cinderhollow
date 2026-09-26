await boot(); G.give({ items: { talon: 1 } });
for (const k of ['boss:coven', 'cut:coven', 'boss:warden', 'cut:warden']) G.SAVE.flags[k] = 1;
for (const k of ['tvcut:TV3:28,7', 'tvcut:TV6:47,7']) G.SAVE.flags[k] = 1;
const tests = [
  ['TV2', 44, 5, 'right', 'TV1'], ['TV1', 2, 3, 'left', 'TV2'], ['TV2', 2, 10, 'left', 'TV3'], ['TV3', 45, 10, 'right', 'TV2'],
  ['TV3', 2, 10, 'left', 'TV4'], ['TV4', 33, 10, 'right', 'TV3'], ['TV4', 2, 10, 'left', 'TV5'], ['TV5', 21, 23, 'right', 'TV4'],
  ['TV5', 21, 9, 'right', 'TV6'], ['TV6', 2, 9, 'left', 'TV5'], ['TV6', 57, 9, 'right', 'TV7'], ['TV7', 2, 9, 'left', 'TV6'],
  ['TV7', 33, 9, 'right', 'TV8'], ['TV8', 3, 10, 'left', 'TV7'],
];
const out = [];
for (const [r, x, y, dir, want] of tests) {
  G.tp(r, x, y); G.enemies.length = 0; G.step(5);
  let got = null;
  for (let i = 0; i < 240 && !got; i++) { G.enemies.length = 0; G.step(1, [dir], i % 20 === 5 ? ['jump'] : []); if (G.room !== r) got = G.room; }
  out.push(`${r}->${want}: ${got === want ? 'OK' : 'FAIL got ' + got + ' at ' + JSON.stringify(G.step(1).p)}`);
}
return out;
