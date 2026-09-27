await boot();
const ids = (window.__ids || ['R1','R2','R3','R4','C1','C2','C3','C6','K1','K2','K3','K4']);
for (const id of ids) { const r = G.step(1); G.tp(id, 3, 10); G.step(30); await snap('old_' + id); }
return 'ok';
