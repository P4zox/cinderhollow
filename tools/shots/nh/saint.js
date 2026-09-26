await boot();
const out = [];
G.give({ items: { talon: 1, wings: 1 } });
G.tp('NH7', 8, 10); G.step(10);
// intro cutscene frames
for (let i = 0; i < 14; i++) { G.step(30); if (i % 2 === 0) await snap('a_intro_' + String(i).padStart(2, '0')); }
for (let i = 0; i < 400 && G.state === 'cut'; i++) G.step(10);
out.push(['after intro', G.state, G.boss && G.boss.state, G.boss && G.boss.active]);
const B = G.boss;
// phase 1: let it act, record moves
G.nhGod(true);
const moves = new Set();
for (let i = 0; i < 60; i++) { G.step(10); if (B.move) moves.add(B.state + ':' + B.move); if (i % 6 === 0) await snap('b_p1_' + String(i).padStart(2, '0')); }
out.push(['p1 moves', [...moves]]);
B.hp = B.maxHp * 0.6; G.step(60);
for (let i = 0; i < 300 && G.state === 'cut'; i++) G.step(10);
out.push(['p2', B.phase, G.state]);
B.cds.delete = 0; B.state = 'idle'; B.cool = 0; B.begin('delete'); 
for (let i = 0; i < 40; i++) { G.step(6); if (i % 5 === 0) await snap('c_p2_del_' + String(i).padStart(2, '0')); }
B.begin('firewall'); for (let i = 0; i < 20; i++) { G.step(8); if (i % 5 === 0) await snap('c_p2_fw_' + String(i).padStart(2, '0')); }
B.hp = B.maxHp * 0.3; for (let i = 0; i < 60; i++) G.step(5);
for (let i = 0; i < 400 && G.state === 'cut'; i++) { G.step(5); if (i % 20 === 0) await snap('d_cut3_' + String(i).padStart(3, '0')); }
out.push(['p3', B.phase, G.state, G.nhRoom().def.biome]);
const m3 = new Set();
for (let i = 0; i < 60; i++) { G.step(10); if (B.move) m3.add(B.state + ':' + B.move); if (i % 6 === 0) await snap('e_p3_' + String(i).padStart(2, '0')); }
out.push(['p3 moves', [...m3]]);
B.hp = 1; B.hit({ dmg: 50, poise: 0, dir: 1, x: B.x, y: B.y - 50 });
for (let i = 0; i < 40; i++) { G.step(10); if (i % 8 === 0) await snap('f_death_' + String(i).padStart(2, '0')); }
out.push(['dead', B.state, G.SAVE.flags['boss:saint0'], G.nhRoom().def.biome]);
return out;
