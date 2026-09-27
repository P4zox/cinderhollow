await boot(); G.SETTINGS.god = 1; const X = G.xrc, log = [];
G.give({ spellsOwned: ['ember_hatchling'], spellsEq: ['ember_hatchling'], spell: 'ember_hatchling' });
G.tp('D9', 18, 37); G.step(20); G.P.fp = 999;
const e0 = G.enemies.filter(e => e.alive).map(e => e.type + ':' + e.hp + '@' + Math.round(e.x/16) + ',' + Math.round(e.y/16));
G.step(1, [], ['cast']);
const tr = [];
for (let i = 0; i < 40; i++) { G.step(15); const c = X.XRC.cub; tr.push(c ? c.state[0] + Math.round(c.t) : '-'); if (i === 8) await snap('cub_fight'); }
log.push(JSON.stringify(e0)); log.push(tr.join(' '));
log.push(JSON.stringify(G.enemies.map(e => e.type + ':' + e.hp)));
return log;
