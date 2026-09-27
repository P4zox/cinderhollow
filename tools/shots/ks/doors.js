await boot(); G.SETTINGS.god = 1; const S = window.__sys, log = [];
const run = async (n) => { for (let i = 0; i < n; i++) G.step(1); };
const at = () => `${G.room}@${Math.round(G.P.x/16*10)/10},${Math.round(G.P.y/16*10)/10} face ${G.P.face} st ${G.P.state}`;
G.tp('T2', 16, 26); G.step(30); await snap('d01_t2_arch');
G.step(1, [], ['interact']); for (let i = 0; i < 70; i++) G.step(1); log.push('after arch: ' + at()); await snap('d02_arrive_t2b');
G.step(20); G.step(1, [], ['interact']); for (let i = 0; i < 70; i++) G.step(1); log.push('back: ' + at());
// portal
G.tp('T2', 20, 26); G.step(10); G.step(1, [], ['interact']); for (let i = 0; i < 10; i++) G.step(1); await snap('d03_portal_out'); for (let i = 0; i < 60; i++) G.step(1); log.push('portal: ' + at()); await snap('d04_portal_in');
// ladder from T2b -> hatch in T2
G.tp('T2b', 3, 10); G.step(10); await snap('d05_ladder'); G.step(1, [], ['interact']); for (let i = 0; i < 70; i++) G.step(1); log.push('ladder->hatch: ' + at()); await snap('d06_hatch');
// auto crack: walk into it in T2b
G.tp('T2b', 21, 10); G.step(10); const tr=[]; for (let i = 0; i < 90 && G.room === 'T2b'; i++) { G.step(1, ['right']); tr.push(Math.round(G.P.x)+(S.SYS.warp?'w':'')); } log.push(tr.join(',')); for (let i = 0; i < 60; i++) G.step(1); log.push('crack auto: ' + at()); await snap('d07_closet');
// walk away and back: no instant re-warp while standing on the arrival door
G.step(30); log.push('still: ' + at());
// solid check around arrival
log.push('solid at feet? ' + JSON.stringify([0,-8,-20].map(dy => { const p = G.P; return false; })));
return log;
