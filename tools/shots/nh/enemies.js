await boot();
const out = [];
window.__nhLog = [];
// NH2: walk up onto rooftop B under the drone
G.tp('NH2', 20, 10); G.step(10);
const d = G.enemies.find(e => e.type === 'nh_drone');
out.push(['drone', d && d.st2, Math.round(d.x), Math.round(d.y)]);
for (let i = 0; i < 60 && d.st2 === 'patrol'; i++) { G.step(4, ['right']); }
out.push(['drone after approach', d.st2, 'enemies', G.enemies.map(e => e.type + ':' + e.state).join(' ')]);
await snap('a_alarm');
for (let i = 0; i < 30; i++) G.step(4);
await snap('b_reinf');
out.push(['after alarm', d.st2, d.called, G.enemies.map(e => e.type + ':' + e.state + ':' + Math.round(e.x)).join(' ')]);
for (let i = 0; i < 100; i++) { G.step(4); if (G.P.hp < 80) G.P.hp = 300; if (i === 30) await snap('c_fight'); }
out.push(['hurt log', window.__nhLog.length, [...new Set(window.__nhLog.map(l => l[2]))].join(',')]);
// NH2 C: turret
window.__nhLog = [];
G.tp('NH2', 44, 12); G.step(10);
const t = G.enemies.find(e => e.type === 'nh_turret');
for (let i = 0; i < 120; i++) { G.step(3); if (i === 40) await snap('d_turret'); if (G.P.hp < 80) G.P.hp = 300; }
out.push(['turret', t.state, 'hits', window.__nhLog.filter(l => l[2] === 'nh_turret').length]);
// kill everything quickly via damage to test deaths
for (const e of G.enemies) if (e.alive) e.hit({ dmg: 9999, poise: 0, dir: 1, x: e.x, y: e.y - 10 });
for (let i = 0; i < 60; i++) G.step(2);
await snap('e_deaths');
out.push(['alive after kill', G.enemies.filter(e => e.alive).length]);
return out;
