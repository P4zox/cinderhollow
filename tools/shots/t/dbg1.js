await boot(); G.give({ items: { talon: 1 } });
G.tp('TV6', 24, 7); G.enemies.length = 0; G.step(10);
const tr = [];
for (let i = 0; i < 90; i++) { G.enemies.length = 0; const P = G.P; const hold = ['right']; const tap = []; if (P.x > 404 && P.ground) tap.push('jump'); if (!P.ground) hold.push('jump'); G.step(1, hold, tap); if (i % 5 == 0) tr.push([Math.round(G.P.x), Math.round(G.P.y), G.P.state]); }
return tr;
