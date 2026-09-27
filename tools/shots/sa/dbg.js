await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.tidebreath = 1;
G.tp('DB13', 22, 21); G.step(10); const A = G.sa, o = [];
o.push('P ' + (G.P.x/16).toFixed(1) + ',' + (G.P.y/16).toFixed(1) + ' ' + G.P.state + ' tile ' + A.tileAt(22, 22));
for (let i = 0; i < 6; i++) { G.step(1, ['down'], ['attack']); G.step(25, ['down']); o.push('tile ' + A.tileAt(22, 22) + ' ' + G.P.state + ' y ' + (G.P.y/16).toFixed(1)); }
for (let i = 0; i < 200 && G.room === 'DB13'; i++) G.step(1, ['down']);
o.push('room ' + G.room);
return o;
