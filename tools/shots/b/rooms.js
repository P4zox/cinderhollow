await boot();
G.give({ items: { hook: 1, talon: 1 } });
G.SAVE.seenAreas = { barrows: 1, cathedral: 1 };
window.__db.SETTINGS.god = true;
const spots = [['K2', 38, 10], ['DB1', 5, 13], ['DB1', 15, 13], ['DB2', 32, 9], ['DB2', 18, 9], ['DB2', 3, 9], ['DB3', 12, 9], ['DB4', 16, 11], ['DB4', 3, 5], ['DB4', 4, 17], ['DB4', 12, 24], ['DB5', 3, 4], ['DB5', 24, 8], ['DB5', 42, 7], ['DB6', 3, 15], ['DB6', 27, 7], ['DB7', 5, 5], ['DB7', 8, 23], ['DB8', 8, 5]];
for (const [r, x, y] of spots) { G.tp(r, x, y); G.step(40); await snap(`r_${r}_${x}_${y}`); }
return 'ok';
