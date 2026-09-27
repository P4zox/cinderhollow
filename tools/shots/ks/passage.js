await boot(); G.SETTINGS.god = 1; const S = window.__sys, log = [];
const cell = () => S.roomObj.grid[25 * S.roomObj.w + 7];
G.tp('T2', 10, 26); G.step(20); log.push('closed, no flag: grid=' + cell() + ' cond=' + S.cond({flag:'x3test:seal',restAfter:true,minTime:300}));
G.SAVE.flags['x3test:seal'] = 1; G.step(40);   // the watcher stamps the time
log.push('flag time ' + S.x3().t['x3test:seal'] + ' play ' + G.SAVE.playTime.toFixed(1));
G.tp('T2', 10, 26); G.step(30); log.push('flag set, not rested: grid=' + cell()); await snap('p01_hint_crack');
// rest at the shrine (interact), close the shrine menu
G.tp('T2', 11, 26); G.step(5); G.step(1, [], ['interact']); for (let i = 0; i < 60; i++) G.step(1); log.push('state after rest: ' + G.state);
for (let i = 0; i < 3 && G.state === 'menu'; i++) { G.step(1, [], ['pause']); G.step(5); }
log.push('restAt ' + S.x3().restAt + ' cond=' + S.cond({flag:'x3test:seal',restAfter:true,minTime:300}));
log.push('still closed until re-entry: grid=' + cell());
G.tp('T2b', 12, 10); G.step(5); G.tp('T2', 10, 26); log.push('re-entered: grid=' + cell() + ' reveal=' + !!S.SYS.reveal);
for (let i = 0; i < 25; i++) G.step(1); await snap('p02_reveal_crack');
for (let i = 0; i < 40; i++) G.step(1); await snap('p03_reveal_open');
// walk through into the closet
for (let i = 0; i < 70; i++) G.step(1, ['left']); log.push('in closet x=' + (G.P.x/16).toFixed(1) + ' thru=' + !!S.x3().seen['x3:T2:seal:thru']);
await snap('p04_closet');
// time path: new flag, no rest, 300 s of play
G.SAVE.flags['x3test:t2'] = 1; G.step(40); const t0 = S.x3().t['x3test:t2'];
log.push('minTime cond before: ' + S.cond({flag:'x3test:t2', minTime: 300})); G.SAVE.playTime += 301; log.push('after 301s: ' + S.cond({flag:'x3test:t2', minTime: 300}) + ' restOnly: ' + S.cond({flag:'x3test:t2', restAfter: true}));
return log;
