await boot(); G.SETTINGS.god = 1; const S = window.__sys, log = [];
const all = ['R1','R2','R3','R4','C1','C2','C2s','C3','C4','C5','K1','K2','K3','K3s','A1','A2','SP1','SP2','HF1','X1','X2'];
for (const r of all) G.SAVE.visited[r] = 1;
S.x3().lore.ks_1 = 10; S.x3().lore.ks_3 = 20; S.x3().lore.ks_2 = 30;
G.tp('K1', 10, 10); G.step(10);
G.step(1, [], ['pause']); G.step(2); G.step(1, [], ['map']); G.step(1, [], ['map']); G.step(3);
log.push('tab ' + (S.menu && S.menu.tab)); await snap('st01_status');
log.push(JSON.stringify(S.completion().tot) + ' pct ' + S.completion().pct);
G.step(1, [], ['spell']); G.step(2);  // back to Inventory
for (let i = 0; i < 6; i++) { G.step(1, [], ['right']); G.step(1); }
log.push('inv cat ' + (S.menu && S.menu.cat)); await snap('st02_inv_lorecat');
G.step(1, [], ['down']); G.step(2); await snap('st03_inv_lorepage');
G.step(1, [], ['confirm']); G.step(30); log.push('reader from inv: ' + S.state); await snap('st04_inv_reader');
G.step(1, [], ['pause']); G.step(2); log.push('back to: ' + S.state + ' tab ' + (S.menu && S.menu.tab));
return log;
