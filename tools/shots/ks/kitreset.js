await boot(); const S = window.__sys, log = [];
const cr = () => { const d = S.roomObj.dyn.find(q => q.kit && q.kit.kind === 'crumble'); return d ? d.kit.st : 'none'; };
G.tp('T2', 32, 26); G.step(5); G.step(1, [], ['interact']); G.step(3);
log.push('start: crumble ' + cr());
G.tp('T2', 51, 15); G.step(3); // teleporting keeps the trial (same room)
log.push('trial after tp: ' + !!S.SYS.trial);
for (let i = 0; i < 90 && S.SYS.trial.attempts === 1; i++) { G.step(1); if (i % 10 == 0) log.push(i + ':' + cr()); } log.push('stood 1.5s: crumble ' + cr() + ' P.y ' + (G.P.y/16).toFixed(1) + ' attempts ' + (S.SYS.trial && S.SYS.trial.attempts));
G.step(60); log.push('later: crumble ' + cr() + ' attempts ' + (S.SYS.trial && S.SYS.trial.attempts) + ' at x ' + (G.P.x/16).toFixed(1));
return log;
