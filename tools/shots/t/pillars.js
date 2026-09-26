await boot(); G.SAVE.flags['cut:warden'] = 1;
G.tp('TV8', 12, 10); G.step(5);
for (let i = 0; i < 200 && !(G.boss && G.boss.active); i++) G.step(2, ['right']);
const b = G.boss; G.step(160); b.x = 40 * 16; b.state = 'idle'; b.cool = 99;
G.P.x = 20 * 16;
G.TVR.pillars = [];
for (const [x, d, a] of [[12, 1, -8], [17, -1, 6], [22, 1, 10], [27, -1, -10], [32, 1, 0]]) G.tvPillar(x * 16, d, 0, a, 36, b);
for (let i = 0; i < 70; i++) { G.P.hp = 999; b.cool = 99; b.state = 'idle'; G.step(1); if (i === 20 || i === 45 || i === 60) await snap('pil_' + i); }
return G.TVR.pillars.length;
