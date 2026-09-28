// the in-game map with every room visited, focused on each RC wing
await boot(); G.grantTechniques();
for (const f of ['boss:cindervane', 'boss:sovereign', 'dp:sluice']) G.SAVE.flags[f] = 1;
const ids = ['SP1','SP2','SP3','SP4','SP5','SP6','SP7','SP8','SP9','SP10','SP11','SP12','SP13','SP14','SP15','SP16','SP17','LF1','D1','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11','D12','D13','D14','D15','D16','D17','X1','X2','X3','X4','X5','X6','X7','X8','X9','X10','X11','X12'];
for (const id of ids) G.SAVE.visited[id] = 1;
const out = [];
for (const [r, x, y] of [['SP8', 20, 17], ['D11', 85, 15], ['X7', 36, 44]]) {
  G.tp(r, x, y); G.step(30); G.step(1, [], ['map']); G.step(10); await snap('map_' + r); out.push(r + ' ' + G.state); G.step(1, [], ['map']); G.step(5); G.step(1, [], ['pause']); G.step(5);
}
return out;
