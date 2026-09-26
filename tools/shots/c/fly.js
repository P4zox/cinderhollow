await boot();
G.SAVE.flags['cut:sanguine'] = 1; G.SAVE.flags['cutp2:sanguine'] = 1;
G.tp('CM7', 6, 14); G.step(30, ['right']);
const B = G.boss, P = G.P;
for (let i = 0; i < 60 && !B.active; i++) G.step(5);
G.step(170); B.hp = Math.floor(B.maxHp * 0.5) - 5; B.state = 'idle'; B.cool = 0.1;
for (let i = 0; i < 700 && !(B.phase === 2 && B.state === 'idle'); i++) G.step(1);
for (let r = 0; r < 3; r++) { P.x = 250; B.x = 450; B.state = 'idle'; B.skyCd = 0; window.__cm.force('fly'); for (let k = 0; k < 150; k++) { G.step(1); P.hp = G.D.maxHp; B.cool = 50; if (k % 25 === 12) await snap(`fly_${r}_${String(k).padStart(3, '0')}`); } }
P.x = 250; B.x = 450; B.state = 'idle'; B.reqCd = 0; window.__cm.force('requiem'); for (let k = 0; k < 300; k++) { G.step(1); P.hp = G.D.maxHp; B.cool = 50; if (k % 20 === 10) await snap(`req_${String(k).padStart(3, '0')}`); }
