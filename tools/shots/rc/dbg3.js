await boot(); G.grantTechniques(); G.SAVE.seenAreas = { deep: 1 }; const log = [];
G.SAVE.charms = ['c_x3_slag']; G.SAVE.charmsEq = ['c_x3_slag'];
G.tp('D2', 8, 10); G.step(30); const hp0 = G.P.hp; const tr = [];
for (let i = 0; i < 90; i++) { G.step(1, ['right']); tr.push(Math.round(G.P.x/16*10)/10 + ',' + Math.round(G.P.y/16*10)/10 + ':' + Math.round(G.P.hp) + G.P.state[0]); }
log.push(tr.filter((_, i) => i % 5 === 0).join(' '));
return log;
