await boot(); G.grantTechniques(); G.SETTINGS.god = 1; G.SAVE.flags['boss:pharaoh'] = 1;
G.tp('DU10', 8, 12); G.step(20);
const ps = G.props.filter(p => p.type === 'sys_passage').map(p => ({ id: p.s && p.s.id, open: p.open }));
const o = ['passages: ' + JSON.stringify(ps)];
for (let k = 0; k < 40 && G.P.x > 40; k++) G.step(3, ['left']);
o.push('walked left to x ' + Math.round(G.P.x) + ' y ' + Math.round(G.P.y));
for (let k = 0; k < 30 && G.room === 'DU10'; k++) { G.step(2, ['up'], ['jump']); G.step(8, ['up']); }
o.push('climbing: now ' + G.room);
return o;
