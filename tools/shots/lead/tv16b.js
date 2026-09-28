await boot(); G.SAVE.items.talon = 1; G.SETTINGS.god = 1; const o = [];
delete G.SAVE.items.emberdash; G.give({});
G.tp('TV9', 104, 11); G.step(20);
const seen = new Set();
for (let k = 0; k < 40; k++) { G.step(4, ['right']); seen.add(G.room + '@' + Math.round(G.P.x)); }
o.push('no dash, pushing east: ended in ' + G.room + ' at ' + Math.round(G.P.x) + ',' + Math.round(G.P.y));
o.push('positions: ' + [...seen].slice(-6).join(' '));
G.step(30, ['left']); o.push('walk back west: ' + G.room + ' ' + Math.round(G.P.x));
return o;
