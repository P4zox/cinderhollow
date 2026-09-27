// every RC door, both ways: use it and check where you land (and that you land standing, not in rock)
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.talon = 1;
const S = window.__sys, log = [];
const pairs = [['SP3', 17, 25, 'SP9'], ['SP9', 43, 10, 'SP3'], ['SP1', 10, 11, 'SP11'], ['SP11', 45, 3, 'SP1'], ['SP6', 16, 5, 'SP13'], ['SP13', 4, 45, 'SP6'],
  ['SP8', 81, 6, 'SP16'], ['SP16', 2, 33, 'SP8'], ['SP8', 104, 7, 'SP16'], ['SP16', 3, 4, 'SP8'], ['SP14', 45, 13, 'SP17'], ['SP17', 2, 11, 'SP14'],
  ['D4', 6, 30, 'D9'], ['D9', 3, 5, 'D4'], ['D7', 4, 14, 'D12'], ['D12', 60, 7, 'D7'], ['D10', 12, 11, 'D14'], ['D14', 3, 10, 'D10'],
  ['D11', 86, 35, 'D15'], ['D15', 3, 12, 'D11'], ['D13', 34, 19, 'D16'], ['D16', 3, 61, 'D13'],
  ['X3', 45, 10, 'X6'], ['X6', 4, 11, 'X3'], ['X4', 21, 10, 'X9'], ['X9', 54, 11, 'X4'], ['LF1', 7, 16, 'SP7']];
for (const [r, x, y, to] of pairs) {
  G.tp(r, x, y); G.step(20);
  const auto = (G.room === r) ? false : true;
  if (G.room === r) { G.step(1, [], ['interact']); for (let i = 0; i < 80; i++) G.step(1); }
  const ok = G.room === to && G.P.ground;
  log.push(`${r}(${x},${y}) -> ${G.room} @${(G.P.x / 16).toFixed(1)},${(G.P.y / 16).toFixed(1)} ground ${G.P.ground} ${ok ? 'OK' : 'FAIL'}`);
}
// SP7: the Last Field passage stays sealed (no door) until Cindervane is dead and you've rested
G.tp('SP7', 30, 15); G.step(20);
log.push('SP7 sealed: door present ' + G.props.some(p => p.type === 'sys_door' && p.s.id === 'lf'));
G.SAVE.flags['boss:cindervane'] = 1; G.step(40); G.tp('SP7', 30, 15); G.step(20);
log.push('SP7 flag, no rest: door ' + G.props.some(p => p.type === 'sys_door' && p.s.id === 'lf'));
S.x3().restAt = G.SAVE.playTime + 1; G.SAVE.playTime += 2; G.tp('SP6', 12, 5); G.step(10); G.tp('SP7', 6, 15); G.step(30);
log.push('SP7 after rest: door ' + G.props.some(p => p.type === 'sys_door' && p.s.id === 'lf'));
await snap('door_sp7_open'); log.push('state ' + G.state); for (let i = 0; i < 20 && G.state !== 'play'; i++) { G.step(1, [], ['pause']); G.step(5); }
for (let i = 0; i < 240 && G.room === 'SP7'; i++) G.step(1, ['left']);
for (let i = 0; i < 60; i++) G.step(1);
log.push('walked into the crack -> ' + G.room + ' ' + (G.P.x / 16).toFixed(1) + ',' + (G.P.y / 16).toFixed(1));
await snap('door_lf_arrive');
return log;
