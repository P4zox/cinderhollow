await boot(); G.SETTINGS.god = 1; const S = window.__sys, log = [];
G.tp('T2', 28, 26); G.step(200);
G.step(1, [], ['interact']); log.push('seated: ' + !!S.SYS.vista + ' state ' + G.P.state + ' zt ' + (S.SYS.vista && S.SYS.vista.zt.toFixed(2)));
G.step(15); await snap('v01_sit_025');
G.step(30); await snap('v02_sit_075');
G.step(60); await snap('v03_sit_175');
G.step(120); await snap('v04_sit_375_lore');
log.push('vistas ' + JSON.stringify(S.x3().vistas) + ' lore ' + JSON.stringify(S.x3().lore));
G.step(1, [], ['jump']); log.push('after key: standing ' + (S.SYS.vista && S.SYS.vista.standing) + ' P ' + G.P.state + ' vy ' + G.P.vy);
G.step(20); await snap('v05_standing');
G.step(60); log.push('vista gone: ' + !S.SYS.vista);
// lore tablet
G.tp('T2', 24, 26); G.step(10); G.step(1, [], ['interact']); G.step(30); log.push('reader: ' + S.state);
await snap('v06_reader');
G.step(1, [], ['confirm']); G.step(2); log.push('closed: ' + S.state);
return log;
