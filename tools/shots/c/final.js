await boot();
G.tp('CM7', 6, 14); G.step(30, ['right']);
for (let i = 0; i < 60; i++) { G.step(8); if (i % 8 === 2) await snap('f_intro_' + String(i).padStart(2, '0')); if (G.state !== 'cut') break; }
const B = G.boss;
B.hp = Math.floor(B.maxHp * 0.5) - 5; B.state = 'idle'; B.cool = 0.1;
for (let i = 0; i < 80; i++) { G.step(6); G.P.hp = G.D.maxHp; if (i % 10 === 3) await snap('f_p2_' + String(i).padStart(2, '0')); }
B.state = 'idle'; B.cool = 99; B.skyCd = 0; window.__cm.force('fly');
for (let i = 0; i < 60; i++) { G.step(4); G.P.hp = G.D.maxHp; if (i % 6 === 2) await snap('f_fly_' + String(i).padStart(2, '0')); }
