await boot(); G.SETTINGS.god = 1; const S = window.__sys, log = [];
G.SAVE.flags['boss:cindervane'] = 1; G.step(40); S.x3().restAt = G.SAVE.playTime + 1; G.SAVE.playTime += 2;
G.tp('SP7', 6, 15); G.step(30);
const r = G.xrc.room; log.push('grid x1 rows 13-15: ' + [13,14,15].map(y => r.grid[y * r.w + 1]) + ' x0: ' + r.grid[15*r.w]);
const tr = []; for (let i = 0; i < 60; i++) { G.step(1, ['left']); tr.push(Math.round(G.P.x) + G.P.state[0] + (S.SYS.warp ? 'W' : '')); }
log.push(tr.join(' ')); log.push('room ' + G.room + ' lock ' + JSON.stringify(S.SYS.doorLock));
return log;
