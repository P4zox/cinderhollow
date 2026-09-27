await boot(); G.SETTINGS.god = 1; const log = [];
const spots = [['SP2', 30, 10], ['SP4', 20, 10], ['SP6', 12, 23], ['SP7', 30, 15], ['SP3', 10, 25], ['D3', 30, 10], ['D5', 24, 10], ['D2', 5, 10], ['D6', 10, 30], ['X3', 20, 10], ['X4', 10, 10], ['X2', 10, 20], ['X1', 5, 10]];
for (const [id, x, y] of spots) { G.tp(id, x, y); G.step(90); await snap('base_' + id); log.push(id); }
return log;
