await boot(); G.SETTINGS.god = 1; const S = window.__sys;
G.tp('R1', 20, 10); G.step(240);
S.spawn({ t: 'sys', kind: 'bench', x: 20, y: 10, id: 'b', view: [30, 5], lore: 'ks_2', skin: 'stone' });
G.step(2); await snap('w01_before');
G.step(1, [], ['interact']);
for (const n of [12, 30, 45, 60, 120]) { for (let i = 0; i < n; i++) G.step(1); await snap('w0' + (n === 12 ? 2 : n === 30 ? 3 : n === 45 ? 4 : n === 60 ? 5 : 6) + '_sit'); }
G.tp('X3', 20, 10); G.step(200); S.spawn({ t: 'sys', kind: 'bench', x: 20, y: 10, id: 'b2', skin: 'wood' }); G.step(2); G.step(1, [], ['interact']); for (let i = 0; i < 150; i++) G.step(1); await snap('w07_crown');
return 'ok';
