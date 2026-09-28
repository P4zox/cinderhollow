await boot(); G.grantTechniques(); G.SAVE.items.talon = 1; G.SETTINGS.god = 1; const o = [];
for (const b of ['coven','warden']) G.SAVE.flags['boss:' + b] = 1;
G.tp('TV9', 104, 11); G.step(20); o.push('start ' + G.room + ' ' + Math.round(G.P.x) + ',' + Math.round(G.P.y) + ' ground ' + G.P.ground);
for (let k = 0; k < 6 && G.room === 'TV9'; k++) { G.step(8, ['right']); G.step(2, ['right'], ['roll']); G.step(20, ['right']); }
o.push('after walking + dashing east: room ' + G.room + ' at ' + Math.round(G.P.x) + ',' + Math.round(G.P.y) + ' hasDash ' + !!G.SAVE.items.emberdash);
return o;
