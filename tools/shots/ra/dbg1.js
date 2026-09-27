await boot(); G.grantTechniques(); G.SETTINGS.god = true;
const out = []; G.tp('R5', 10, 0); G.step(2);
for (let i = 0; i < 70; i++) { G.step(1, i < 30 ? ['jump'] : [], i === 0 ? ['jump'] : []); if (i % 3 == 0) out.push(`${i} ${G.room} ${(G.P.x/16).toFixed(2)},${(G.P.y/16).toFixed(2)} vy=${G.P.vy.toFixed(0)} g=${G.P.ground} ${G.P.state}`); }
return out;
