await boot(); G.grantTechniques(); G.SETTINGS.god = 0; const o = [];
G.tp('R11', 19, 5); G.step(60); const ledge = [Math.round(G.P.x), Math.round(G.P.y)];
G.P.hp = 9999; let hits = 0, h0 = G.P.hp;
G.P.x = 104; G.P.y = 360; G.P.vy = 0;   // fall into the mist
for (let f = 0; f < 600; f++) { G.step(1); if (G.P.hp < h0) hits++; h0 = G.P.hp; }
o.push(`ledge ${ledge}; hits in 10 s: ${hits}; back at ${Math.round(G.P.x)},${Math.round(G.P.y)}`);
return o;
