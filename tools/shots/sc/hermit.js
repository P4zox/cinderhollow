// H1's hidden path: sealed until Oswin has fallen, then open both ways; walk H1 -> H2 -> H3 and back
await boot(); G.SETTINGS.god = 1; const out = [];
G.SAVE.flags['sc:seal'] = 1;
G.tp('H1', 3, 10); G.step(30);
for (let i = 0; i < 120; i++) G.step(1, ['left']); out.push('before Oswin: room ' + G.room + ' x ' + (G.P.x / 16).toFixed(1));
G.SAVE.flags['boss:oswin'] = 1;
G.tp('H1', 3, 10); G.step(60); await snap('h1_open');
for (let i = 0; i < 240 && G.room === 'H1'; i++) G.step(1, ['left']); out.push('after: ' + G.room);
for (let i = 0; i < 900 && G.room !== 'H3'; i++) { const r = G.step(1, ['left'], (i % 20 === 0) ? ['jump'] : []); }
out.push('reached ' + G.room);
for (let i = 0; i < 1400 && G.room !== 'H1'; i++) G.step(1, ['right'], (i % 20 === 0) ? ['jump'] : []);
out.push('back to ' + G.room);
return out;
