await boot(); G.grantTechniques(); G.SETTINGS.god = 0;
const o = [];
// walk the tower route: stand on the Perch's high ledge, then step off into the mist drop
G.tp('R11', 20, 8); G.step(30); o.push('start ' + G.P.x + ',' + G.P.y + ' hp ' + Math.round(G.P.hp));
G.P.hp = 9999; let hits = 0, h0 = G.P.hp;
G.tp('R11', 6, 22); for (let f = 0; f < 600; f++) { G.step(1); if (G.P.hp < h0) { hits++; } h0 = G.P.hp; }
o.push('hits over 10s after dropping into the mist: ' + hits + ' now at ' + Math.round(G.P.x) + ',' + Math.round(G.P.y));
// leave the room and make sure the void does not follow
G.tp('R1', 10, 10); G.P.hp = 9999; h0 = G.P.hp; let ghost = 0; for (let f = 0; f < 300; f++) { G.step(1); if (G.P.hp < h0) ghost++; h0 = G.P.hp; }
G.tp('R5', 10, 18); for (let f = 0; f < 300; f++) { G.step(1); if (G.P.hp < h0) ghost++; h0 = G.P.hp; }
o.push('phantom hits in other rooms: ' + ghost);
return o;
