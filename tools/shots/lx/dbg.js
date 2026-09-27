await boot(); G.SETTINGS.god = 1;
G.tp('C2', 24, 10); G.enemies.length = 0; G.SETTINGS.light = 2; G.step(30);
const L = G.lx.LX, M = L.map, o = [];
o.push('map ' + M.w + 'x' + M.h + ' n=' + L.n);
const B = 8, ptx = Math.floor(G.P.x / 16) + B, pty = Math.floor((G.P.y - 1) / 16) + B;
for (let y = pty - 3; y <= pty + 2; y++) { let r = ''; for (let x = ptx - 6; x <= ptx + 6; x++) r += M.sol[y * M.w + x] ? '#' : '.'; o.push(r); }
o.push('LP0 ' + Array.from(L.LP.slice(0, 8)).map(v => v.toFixed(1)) + ' LC0 ' + Array.from(L.LC.slice(0, 8)).map(v => v.toFixed(2)));
o.push('P ' + G.P.x + ',' + G.P.y + ' cam ' + L.cx + ',' + L.cy);
for (const d of [1, 2, 3]) { L.dbg = d; G.step(1); await snap('dbg' + d); } L.dbg = 0;
for (const m of [1, 2]) { G.SETTINGS.light = m; G.step(1); await snap('fin' + m); L.dbg = 3; G.step(1); await snap('fl' + m); L.dbg = 0; }
return o;
