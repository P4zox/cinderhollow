await boot();
G.SAVE.flags['cut:coven'] = 1;
G.tp('TV4', 31, 10); G.step(5);
for (let i = 0; i < 60 && !(G.boss && G.boss.active); i++) G.step(2, ['left']);
const log = [];
for (let i = 0; i < 600; i++) { G.P.hp = 999; G.step(1); if (i % 60 === 0) log.push(G.boss.parts.map(q => `${q.state}:${Math.round(q.x)}->${Math.round(G.boss.slotX(q))}`).join(' ') + ' P' + Math.round(G.P.x)); }
return log;
