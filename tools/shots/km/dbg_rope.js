await boot(); G.SETTINGS.god = true; const out = [];
G.tp('T1', 27, 32); 
const r = G.KIT.objs.filter(q => q.kind === 'swing');
for (let i = 0; i < 10; i++) { G.step(20); out.push(r.map(q => q.ang.toFixed(2) + '/' + q.av.toFixed(2)).join(' ') + ' P ' + G.P.state); }
return out;
